import json
import logging
import math
from datetime import timedelta

import requests
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

from aktionen.models import Aktion, Category
from core.all_messages import all_messages
from family.models import Family
from personals.models import UserErweitert
from utils.functions import (
    WORLDWIDE_RANKING_NAME,
    clean_html,
    create_internal_error,
    create_notification,
    generate_random_password,
    get_all_klimapunkte_from_user,
    get_communities_of_user,
    get_families_of_user,
    ist_email_gueltig,
    send_mail_function,
)

from .models import IOSDevice
from .tokens import email_verification_token

logger = logging.getLogger(__name__)

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_MIN_SCORE = 0.5
RECAPTCHA_TIMEOUT_SECONDS = 10
RELOGIN_AFTER_DAYS = 2
MAX_WEEKLY_GOAL = 100_000
SUPPORTED_LANGUAGES = ("de", "en")
STATISTICS_DEFAULT_DAYS = 30
STATISTICS_MAX_DAYS = 3650
STATISTICS_DAY_OPTIONS = [7, 30, 365]
ACTIVATION_MAIL_SUBJECT = "ClimateQuest - dein Aktivierungslink ist da!"
USERNAME_MAX_LENGTH = User._meta.get_field("username").max_length
MAX_DEVICE_FIELD_LENGTH = 200


def generate_verification_link(request):
    user = request.user
    return request.build_absolute_uri(
        reverse(
            "activate",
            kwargs={
                "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": email_verification_token.make_token(user),
            },
        )
    )


def send_activation_mail(request, user, recipient, error_message=None):
    link = generate_verification_link(request)
    options = {"fehlermeldung": error_message} if error_message else {}
    return send_mail_function(
        request=request,
        subject=ACTIVATION_MAIL_SUBJECT,
        message=_("Bitte klick auf den folgenden Link, um deine E-Mail-Adresse zu verifizieren: %(activation_link)s")
        % {"activation_link": link},
        recipient_list=recipient,
        mailinglist_needless=True,
        user=user,
        **options,
    )


def login_view(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next")
            if not next_url or not url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                next_url = "dashboard"
            messages.info(request, "logged-in")
            return redirect(next_url)
        messages.error(request, all_messages["invalid_login_data"])
        return redirect("login_view")
    return render(request, "./login.html", {"next": request.GET.get("next", "")})


def logout_view(request):
    logout(request)
    return redirect("home")


def recaptcha_passed(token):
    """Verify a reCAPTCHA v3 token; a failing verification service counts as "not passed"."""
    try:
        response = requests.post(
            RECAPTCHA_VERIFY_URL,
            data={"secret": settings.RECAPTCHA_PRIVATE_KEY, "response": token},
            timeout=RECAPTCHA_TIMEOUT_SECONDS,
        )
        result = response.json()
    except (requests.RequestException, ValueError):
        logger.exception("reCAPTCHA verification failed")
        return False
    return bool(result.get("success")) and result.get("score", 0) >= RECAPTCHA_MIN_SCORE


def register_view(request):
    if request.method != "POST":
        return render(request, "./register.html")

    recaptcha_token = request.POST.get("recaptchaToken")
    if not recaptcha_token:
        messages.error(request, all_messages["recaptcha_token_missing"])
        return redirect("register_view")
    if not recaptcha_passed(recaptcha_token):
        messages.error(request, all_messages["robot"])
        return redirect("register_view")

    username = request.POST.get("username")
    password = request.POST.get("password")
    email = request.POST.get("email") or ""

    if request.POST.get("nutzungsbedingungen_accepted") != "on":
        messages.error(request, all_messages["nutzungsbedingungen_not_accepted"])
        return redirect("register_view")
    if request.POST.get("datenschutz_accepted") != "on":
        messages.error(request, all_messages["datenschutz_not_accepted"])
        return redirect("register_view")
    if not username or not password:
        messages.error(request, all_messages["missing_required_inputs"])
        return redirect("register_view")
    if len(username) > USERNAME_MAX_LENGTH:
        messages.error(request, all_messages["too_long_input"])
        return redirect("register_view")
    if User.objects.filter(username=username).exists():
        messages.error(request, all_messages["username_not_available"])
        return redirect("register_view")
    if email:
        if not ist_email_gueltig(email):
            messages.error(request, all_messages["invalid_email"])
            return redirect("register_view")
        if User.objects.filter(email=email).exists():
            messages.error(request, all_messages["email_not_available"])
            return redirect("register_view")

    with transaction.atomic():
        user = User.objects.create_user(username=username, password=password, email=email)
        actions_after_registration(request, user)
        UserErweitert.objects.filter(user=user).update(mail_verified=not email)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    if not email:
        messages.success(request, all_messages["successfully_signed_up"])
        messages.info(request, "logged-in")
        return redirect("dashboard")

    messages.success(request, all_messages["successfully_signed_up_email_not_verified"])
    messages.info(request, "logged-in")
    send_activation_mail(
        request,
        user,
        email,
        _(
            "Fehler beim E-Mail-Versand. Probiere die Registrierung ohne E-Mail und füge deine E-Mail-Adresse "
            "später in den Einstellungen hinzu."
        ),
    )
    return redirect("dashboard")


def activate(request, uidb64, token):
    try:
        user = get_user_model().objects.get(pk=urlsafe_base64_decode(uidb64).decode())
    except (TypeError, ValueError, OverflowError, UnicodeDecodeError, get_user_model().DoesNotExist):
        user = None

    if user and email_verification_token.check_token(user, token):
        UserErweitert.objects.filter(user=user).update(mail_verified=True)
        messages.success(request, all_messages["email_verified"])
    else:
        messages.error(request, all_messages["invalid_verification_link"])
    return redirect("dashboard")


@login_required
def resend_verification_email(request):
    if request.user.email == "":
        messages.error(request, all_messages["no_email_to_verify"])
        return redirect("settings_view")

    send_activation_mail(
        request,
        request.user,
        request.user.email,
        _("Fehler beim E-Mail-Versand. Probiere es später erneut."),
    )
    messages.success(request, all_messages["verification_email_resent"])
    return redirect("settings_view")


def _change_username(request):
    new_username = request.POST.get("new_username")
    if not new_username:
        messages.error(request, all_messages["missing_required_inputs"])
    elif len(new_username) > USERNAME_MAX_LENGTH:
        messages.error(request, all_messages["too_long_input"])
    elif new_username == request.user.username:
        messages.error(request, all_messages["username_belongs_to_you"])
    elif User.objects.filter(username=new_username).exists():
        messages.error(request, all_messages["username_not_available"])
    else:
        request.user.username = new_username
        request.user.save()
        messages.success(request, all_messages["username_changed"])


def _change_password(request):
    new_password = request.POST.get("new_password")
    if not new_password:
        messages.error(request, all_messages["missing_required_inputs"])
        return
    request.user.set_password(new_password)
    request.user.save()
    update_session_auth_hash(request, request.user)
    messages.success(request, all_messages["password_changed"])


def _change_email(request):
    email = request.POST.get("email") or ""
    if email == "":
        request.user.email = ""
        request.user.save()
        messages.success(request, all_messages["successfully_changed_email_no_email"])
        return
    if not ist_email_gueltig(email):
        messages.error(request, all_messages["invalid_email"])
        return
    if User.objects.filter(email=email).exists():
        messages.error(request, all_messages["email_not_available"])
        return

    old_email = request.user.email
    request.user.email = email
    request.user.save()
    UserErweitert.objects.filter(user=request.user).update(mail_verified=False)

    if send_activation_mail(request, request.user, email):
        messages.success(request, all_messages["email_changed"])
    else:
        request.user.email = old_email
        request.user.save()
        UserErweitert.objects.filter(user=request.user).update(mail_verified=True)


def _change_weekly_goal(request):
    """Returns the view to show next: the dashboard if the goal was changed."""
    try:
        weekly_goal = int(request.POST.get("weekly_goal"))
    except (TypeError, ValueError):
        messages.error(request, all_messages["not_a_number"])
        return None
    if weekly_goal < 1:
        messages.error(request, all_messages["weekly_goal_too_small"])
        return None
    if weekly_goal > MAX_WEEKLY_GOAL:
        messages.error(request, all_messages["weekly_goal_too_large"])
        return None
    UserErweitert.objects.filter(user=request.user).update(weekly_goal=weekly_goal)
    messages.success(request, all_messages["successfully_changed_goal"])
    return "dashboard"


def _change_language(request):
    lang = request.POST.get("lang")
    if lang not in SUPPORTED_LANGUAGES:
        messages.error(request, all_messages["internal_error"])
        return
    UserErweitert.objects.filter(user=request.user).update(lang=lang)
    messages.success(request, "Sprache erfolgreich geändert" if lang == "de" else "Language successfully changed")


def _change_boolean_setting(request, field, form_field, enabled_message, disabled_message):
    value = request.POST.get(form_field) == "on"
    UserErweitert.objects.filter(user=request.user).update(**{field: value})
    messages.success(request, all_messages[enabled_message if value else disabled_message])


def _delete_account(request):
    """Notify everybody who shares a family or community with the user, then delete the account."""
    user = request.user
    other_members = User.objects.exclude(id=user.id)
    # Users that only share the worldwide ranking are not notified.
    family_members = other_members.filter(
        families__in=get_families_of_user(user).exclude(name=WORLDWIDE_RANKING_NAME)
    ).distinct()
    community_members = other_members.filter(families__communities__in=get_communities_of_user(user)).distinct()
    community_members = community_members.exclude(id__in=family_members.values("id"))

    for member in family_members:
        create_notification(
            request,
            f"User {user.username}, mit dem / der du zusammen in einer Family warst, hat den eigenen Account "
            f"gelöscht. Von {user.username} gesendete Nachrichten werden auch gelöscht.",
            f"User {user.username}, who you were in a family with, has deleted their account. "
            "Their messages will also be deleted.",
            member,
        )
    for member in community_members:
        create_notification(
            request,
            f"User {user.username}, mit dem / der du zusammen in einer Community warst, hat den eigenen Account "
            f"gelöscht. Von {user.username} gesendete Nachrichten werden auch gelöscht.",
            f"User {user.username}, who you were in a community with, has deleted their account. "
            "Their messages will also be deleted.",
            member,
        )
    user.delete()
    logout(request)
    messages.error(request, all_messages["account_deleted"])
    return "login_view"


def _change_statement(request):
    UserErweitert.objects.filter(user=request.user).update(statement=clean_html(request.POST.get("content") or ""))
    messages.success(request, all_messages["successfully_changed_statement"])


# POST button name -> handler. A handler may return the name of a view to redirect to instead of the settings page.
SETTINGS_ACTIONS = {
    "change_username": _change_username,
    "change_password": _change_password,
    "change_email": _change_email,
    "change_email_settings": lambda request: _change_boolean_setting(
        request, "mailinglist", "mailinglist", "mailinglist_enabled", "mailinglist_disabled"
    ),
    "change_block_data_settings": lambda request: _change_boolean_setting(
        request, "allows_data_view", "block_data_settings", "allows_data_view_enabled", "allows_data_view_disabled"
    ),
    "change_statement": _change_statement,
    "change_weekly_goal": _change_weekly_goal,
    "change_lang": _change_language,
    "change_tour_banner": lambda request: _change_boolean_setting(
        request, "show_tour_banner", "show_tour_banner", "activated_tour_banner", "deactivated_tour_banner"
    ),
    "delete_account": _delete_account,
}


@login_required
def settings_view(request):
    last_login = request.user.last_login
    relogin_before = timezone.localdate() - timedelta(days=RELOGIN_AFTER_DAYS)
    if last_login is not None and timezone.localtime(last_login).date() < relogin_before:
        messages.success(request, all_messages["relogin_to_edit"])
        return redirect("login_view")

    if request.method == "POST":
        for button, handler in SETTINGS_ACTIONS.items():
            if button in request.POST:
                return redirect(handler(request) or "settings_view")

    return render(
        request,
        "./personal_settings.html",
        {"is_social_account": SocialAccount.objects.filter(user=request.user).exists()},
    )


def reset_password(request):
    if request.method != "POST":
        return render(request, "reset_password.html")

    email = request.POST.get("email")
    user = User.objects.filter(email=email).first() if email else None
    if user is None:
        messages.error(request, all_messages["email_not_found"])
        return redirect("reset_password")
    if SocialAccount.objects.filter(user=user).exists():
        messages.error(request, all_messages["socialaccount_no_password_reset"])
        return redirect("reset_password")

    new_password = generate_random_password()
    sent = send_mail_function(
        request=request,
        subject="ClimateQuest - Passwort Reset",
        message=_(
            "Wir haben dir ein neues, zufällig generiertes Passwort erstellt: <b>%(new_password)s</b> \n"
            "Melde dich damit und mit deinem Usernamen <b>%(username)s</b> "
            '<a href="https://climate-quest.de/personals/login/">hier</a> an und ändere aus Sicherheitsgründen '
            'möglichst bald unter "Profil bearbeiten" dein Passwort.'
        )
        % {"new_password": new_password, "username": user.username},
        recipient_list=user.email,
        mailinglist_needless=True,
        user=user,
    )
    if not sent:
        return redirect("reset_password")

    user.set_password(new_password)
    user.save()
    messages.success(request, all_messages["password_reset_mail_sent"])
    return redirect("login_view")


def actions_after_registration(request, user):
    """Put a new user into the worldwide ranking and create the extended profile."""
    worldwide = Family.objects.filter(name=WORLDWIDE_RANKING_NAME).first()
    if worldwide is None:
        create_internal_error(request, f'Family "{WORLDWIDE_RANKING_NAME}" existiert nicht')
    else:
        worldwide.members.add(user)
    UserErweitert.objects.create(user=user, lang=getattr(request, "LANGUAGE_CODE", settings.LANGUAGE_CODE))


def check_username(request):
    return JsonResponse({"exists": User.objects.filter(username=request.GET.get("username")).exists()})


def check_email(request):
    return JsonResponse({"exists": User.objects.filter(email=request.GET.get("email")).exists()})


@login_required
def get_email_settings(request):
    return JsonResponse({"mailinglist": request.user.usererweitert.mailinglist})


@login_required
def get_block_data_settings(request):
    return JsonResponse({"block_data_settings": request.user.usererweitert.allows_data_view})


def _credit_overview(user, klimapunkte_for_credit):
    klimapunkte = get_all_klimapunkte_from_user(user)
    available = math.floor(klimapunkte / klimapunkte_for_credit - user.usererweitert.given_credits)
    rest = klimapunkte % klimapunkte_for_credit
    return available, int(rest / klimapunkte_for_credit * 100), klimapunkte_for_credit - rest


@login_required
def credit_view(request):
    klimapunkte_for_credit = request.GLOBAL_VARIABLES["klimapunkte_for_credit"]

    if request.method == "POST":
        with transaction.atomic():
            # Lock the profile so that a double click cannot plant more trees than the user has credits for.
            profile = UserErweitert.objects.select_for_update().get(user=request.user)
            available_credits, _percent, _missing = _credit_overview(request.user, klimapunkte_for_credit)
            if available_credits > 0 and not profile.plant_tree():
                create_internal_error(
                    request,
                    f"{all_messages['error_planting_tree']} (vermutlich sind keine Baumcodes mehr vorhanden)",
                    all_messages["error_planting_tree"],
                )
        return redirect("credit_view")

    available_credits, percent_done, klimapunkte_missing = _credit_overview(request.user, klimapunkte_for_credit)
    return render(
        request,
        "./credit_view.html",
        {
            "available_credits": available_credits,
            "percent_done": percent_done,
            "klimapunkte_missing": klimapunkte_missing,
        },
    )


@csrf_exempt
def register_ios_device(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        user_id = data.get("user_id")
        apns_token = data.get("apns_token")
        bundle_id = data.get("bundle_id", "")
        app_version = data.get("app_version", "")
    except (ValueError, AttributeError):
        return JsonResponse({"error": "invalid json"}, status=400)

    if not user_id or not apns_token:
        return JsonResponse({"error": "user_id and apns_token required"}, status=400)
    fields = (apns_token, bundle_id, app_version)
    if not all(isinstance(value, str) and len(value) <= MAX_DEVICE_FIELD_LENGTH for value in fields):
        return JsonResponse({"error": "invalid device data"}, status=400)

    user = User.objects.filter(pk=user_id).first() if str(user_id).isdecimal() else None
    if user is None:
        return JsonResponse({"error": "user not found"}, status=404)

    device, _created = IOSDevice.objects.update_or_create(
        apns_token=apns_token, defaults={"user": user, "bundle_id": bundle_id, "app_version": app_version}
    )
    return JsonResponse({"status": "ok", "device_id": device.id})


def _statistics_days(request):
    try:
        days = int(request.GET.get("days", STATISTICS_DEFAULT_DAYS))
    except ValueError:
        return STATISTICS_DEFAULT_DAYS
    return days if 1 <= days <= STATISTICS_MAX_DAYS else STATISTICS_DEFAULT_DAYS


@login_required
def statistics_view(request):
    days = _statistics_days(request)
    since = timezone.localdate() - timedelta(days=days)
    name_field = "name" if request.LANGUAGE_CODE == "de" else "name_en"

    rows = (
        Aktion.objects.filter(user=request.user, date__gte=since)
        .annotate(category_name=F(f"aktion__category__{name_field}"))
        .values("date", "category_name")
        .annotate(points=Sum(F("quantity") * F("aktion__klimapunkte")))
        .order_by("date")
    )
    categories = list(Category.objects.values_list(name_field, flat=True))
    dates = sorted({str(row["date"]) for row in rows})

    points = {category: dict.fromkeys(dates, 0) for category in categories}
    for row in rows:
        if row["category_name"] in points:
            points[row["category_name"]][str(row["date"])] = round(row["points"], 2)

    chart_data = {
        "labels": dates,
        "categories": categories,
        "series": [list(points[category].values()) for category in categories],
    }
    return render(
        request,
        "./statistics.html",
        {
            "chart_data": json.dumps(chart_data).replace("<", "\\u003c"),
            "days": days,
            "days_options": STATISTICS_DAY_OPTIONS,
        },
    )
