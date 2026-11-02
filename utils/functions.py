import logging
import re
import secrets
import string
import time
import traceback
from datetime import date, timedelta

import bleach
import httpx
import jwt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.db.models import Count, F, QuerySet, Sum
from django.db.models.functions import TruncWeek
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.translation import gettext as _
from webpush import send_user_notification

from aktionen.models import Aktion, Category
from artikel.models import Artikel
from community.models import Community
from core.all_messages import all_messages
from family.models import Family
from hall_of_fame.models import HallOfFameEntry
from home.models import Benachrichtigung
from personals.models import IOSDevice, Level, UserErweitert

QUANTITY_DECIMAL_PLACES = 4
KLIMAPUNKTE_PER_LIKE = 0.1
WORLDWIDE_RANKING_NAME = "worldwide ranking"
PASSWORD_LENGTH = 12
PASSWORD_ALPHABET = string.ascii_letters + string.digits + string.punctuation.replace('"', "").replace("'", "")
APNS_TIMEOUT_SECONDS = 10
PUSH_TTL_SECONDS = 1000

logger = logging.getLogger(__name__)


def generate_random_password():
    """Random password that contains no quotes, so it cannot terminate a quoted string."""
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(PASSWORD_LENGTH))


MAIL_STYLE = """
      body { margin: 0; padding: 0; background: #f5f7fa;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1f2937; line-height: 1.5; }
      .container { max-width: 600px; margin: 24px auto; background: #ffffff; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); overflow: hidden; }
      .header { padding: 20px 24px; border-bottom: 1px solid #e5e7eb; }
      .header h1 { font-size: 20px; margin: 0; color: #14532d; }
      .content { padding: 24px; font-size: 16px; }
      .footer { padding: 16px 24px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280;
        background: #f9fafb; }
"""

MAIL_UNSUBSCRIBE_FOOTER = (
    "<p>Du erhältst diese E-Mail, weil du <i>Benachrichtigungen auch per E-Mail erhalten</i> aktiviert hast "
    '<a href="https://climate-quest.de/personals/settings/#mailinglist_checkbox">Hier abmelden</a>.</p>'
)
MAIL_LEGAL_FOOTER = (
    '<p><a href="https://climate-quest.de/impressum/">Impressum</a> • '
    '<a href="https://climate-quest.de/datenschutz/">Datenschutz</a></p>'
)


def build_mail_html(subject, message, url, include_unsubscribe):
    """HTML body of a notification mail. ``message`` is trusted HTML, ``subject`` and ``url`` are escaped."""
    footer = (MAIL_UNSUBSCRIBE_FOOTER if include_unsubscribe else "") + MAIL_LEGAL_FOOTER
    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width">
    <title>{escape(subject)}</title>
    <style>{MAIL_STYLE}</style>
  </head>
  <body>
    <div class="container">
      <div class="header"><h1>{escape(subject)}</h1></div>
      <div class="content">{message} <a href="{escape(url)}">Mehr</a></div>
      <div class="footer">{footer}</div>
    </div>
  </body>
</html>"""


def send_mail_function(**kwargs):
    """Send a notification mail.

    Returns True when nothing needed to be sent or the mail was sent, and False when the user has
    unsubscribed from mails or sending failed.
    """
    request = kwargs.get("request")
    fehlermeldung = kwargs.get("fehlermeldung", "Fehler beim E-Mail-Versand")
    subject = kwargs.get("subject")
    message = kwargs.get("message")
    mailinglist_needless = kwargs.get("mailinglist_needless", False)
    url = kwargs.get("url", "/dashboard/")

    if subject is None or message is None:
        create_internal_error(
            request, "Beim E-Mail Versand wurden nicht alle notwendigen Elemente übergeben", fehlermeldung
        )
        return False

    user = kwargs.get("user") or getattr(request, "user", None)
    if user is None:
        create_internal_error(request, "Bei send_mail_function wurde kein User übergeben", fehlermeldung)
        return False

    recipient = kwargs.get("recipient_list") or user.email

    if not mailinglist_needless:
        if user.email == "":
            return True
        try:
            user_erweitert = UserErweitert.objects.get(user=user)
        except UserErweitert.DoesNotExist:
            create_internal_error(request, f"UserErweitert zu User {user} nicht gefunden", fehlermeldung)
            return False
        if not user_erweitert.mail_verified:
            return True
        if not user_erweitert.mailinglist:
            return False

    try:
        email = EmailMultiAlternatives(
            subject=subject, body=message, from_email=settings.DEFAULT_FROM_EMAIL, to=[recipient]
        )
        email.attach_alternative(build_mail_html(subject, message, url, not mailinglist_needless), "text/html")
        email.send()
    except Exception as e:  # noqa: BLE001 - any SMTP/network failure must not break the calling request
        create_internal_error(request, f"Fehler beim E-Mail-Versand an {recipient}: {e}", fehlermeldung, exception=e)
        return False
    return True


def get_klimapunkte(aktionen):
    """Sum of climate points of the given actions (a queryset is summed in the database)."""
    if isinstance(aktionen, QuerySet):
        return aktionen.aggregate(total=Sum(F("quantity") * F("aktion__klimapunkte")))["total"] or 0
    return sum(aktion.impact for aktion in aktionen)


def get_klimapunkte_from_likes(user):
    likes = Artikel.objects.filter(creator=user).aggregate(likes=Count("like"))["likes"]
    return likes * KLIMAPUNKTE_PER_LIKE


def get_additional_klimapunkte(user):
    return get_klimapunkte_from_likes(user) + user.usererweitert.additional_klimapunkte


def get_all_klimapunkte_from_user(user):
    return get_klimapunkte(Aktion.objects.filter(user=user)) + get_additional_klimapunkte(user)


def get_level(user, klimapunkte=None):
    """Level information for ``user`` (or for an already known number of climate points)."""
    if klimapunkte is None:
        klimapunkte = get_all_klimapunkte_from_user(user)
    levels = list(Level.objects.order_by("klimapunkte"))

    current_level = None
    next_level = levels[0] if levels else None
    level_number = 0
    progress_percent = 100 if not levels else 0

    for i, level in enumerate(levels):
        if klimapunkte < level.klimapunkte:
            break
        current_level = level
        level_number = i + 1
        if i + 1 == len(levels):
            return {
                "info": _('Du hast das höchste Level bereits erreicht: %(level)s <span class="emoji">&#x1F973;</span>')
                % {"level": current_level.description},
                "current_level": current_level,
                "levels": levels,
                "klimapunkte": klimapunkte,
                "level_number": level_number,
            }
        next_level = levels[i + 1]
        difference = next_level.klimapunkte - current_level.klimapunkte
        progress = klimapunkte - current_level.klimapunkte
        progress_percent = int(progress / difference * 100) if difference > 0 else 100

    return {
        "current_level": current_level,
        "next_level": next_level,
        "progress_percent": progress_percent,
        "levels": levels,
        "klimapunkte_missing": next_level.klimapunkte - klimapunkte if next_level else 0,
        "level_number": level_number,
    }


def get_weekly_goal_from_user(user):
    weekly_goal = user.usererweitert.weekly_goal
    today = timezone.localdate()
    weekly_klimapunkte = get_klimapunkte(Aktion.objects.filter(user=user, date__gte=_week_start(today)))
    return weekly_goal, weekly_klimapunkte, round(weekly_klimapunkte / weekly_goal * 100)


def _week_start(day):
    return day - timedelta(days=day.weekday())


def get_streak_from_user(user):
    """Number of consecutive weeks (ending this or last week) in which the weekly goal was reached."""
    weekly_goal = user.usererweitert.weekly_goal
    weekly_data = list(
        Aktion.objects.filter(user=user)
        .annotate(week=TruncWeek("date"))
        .values("week")
        .annotate(total_impact=Sum(F("aktion__klimapunkte") * F("quantity")))
        .order_by("-week")
    )

    current_week_start = _week_start(timezone.localdate())
    last_week_start = current_week_start - timedelta(weeks=1)

    successful_weeks = 0
    expected_week = (
        current_week_start if weekly_data and weekly_data[0]["week"] == current_week_start else last_week_start
    )

    for entry in weekly_data:
        week_start = entry["week"]
        reached_goal = entry["total_impact"] >= weekly_goal
        if week_start == current_week_start and not reached_goal:
            expected_week = last_week_start  # the running week may still be completed
            continue
        if week_start != expected_week or not reached_goal:
            break
        successful_weeks += 1
        expected_week -= timedelta(weeks=1)

    return successful_weeks


def get_perfect_week_progress(user, date_given):
    """Which categories have at least one action in the week of ``date_given`` (by German and English name)."""
    week_start = _week_start(date_given)
    covered_category_ids = set(
        Aktion.objects.filter(user=user, date__range=(week_start, week_start + timedelta(days=6)))
        .values_list("aktion__category_id", flat=True)
        .distinct()
    )
    categories = list(Category.objects.all())
    return (
        {category.name: category.id in covered_category_ids for category in categories},
        {category.name_en: category.id in covered_category_ids for category in categories},
    )


def get_date_range(zeitraum: str, heute: date) -> tuple[date | None, date | None]:
    offsets = {
        "Heute": timedelta(days=0),
        "Sieben Tage": timedelta(days=7),
        "Dreißig Tage": timedelta(days=30),
        "Dreihundertfünfundsechzig Tage": timedelta(days=365),
    }
    if zeitraum in offsets:
        return heute - offsets[zeitraum], heute
    return None, None


def get_klimapunkte_for_member(member, start: date | None, end: date | None):
    aktionen = Aktion.objects.filter(user=member)
    if start is not None:
        aktionen = aktionen.filter(date__gte=start)
    if end is not None:
        aktionen = aktionen.filter(date__lte=end)
    return get_klimapunkte(aktionen)


def get_hall_of_fame_entries(user: User) -> int:
    return HallOfFameEntry.objects.filter(user=user).count()


def get_klimapunkte_by_user(user_ids, start=None, end=None, include_additional=True):
    """``{user_id: climate points}`` for all given users using a constant number of queries.

    Actions are limited to ``start``..``end`` (inclusive, either may be None). With ``include_additional`` the
    bonus points and article likes of every user are added regardless of the period.
    """
    totals = dict.fromkeys(user_ids, 0.0)
    actions = Aktion.objects.filter(user__in=totals)
    if start is not None:
        actions = actions.filter(date__gte=start)
    if end is not None:
        actions = actions.filter(date__lte=end)
    for row in actions.values("user_id").annotate(total=Sum(F("quantity") * F("aktion__klimapunkte"))):
        totals[row["user_id"]] += row["total"]
    if include_additional:
        for user_id, additional in UserErweitert.objects.filter(user__in=totals).values_list(
            "user_id", "additional_klimapunkte"
        ):
            totals[user_id] += additional
        for row in Artikel.objects.filter(creator__in=totals).values("creator_id").annotate(likes=Count("like")):
            totals[row["creator_id"]] += row["likes"] * KLIMAPUNKTE_PER_LIKE
    return totals


def get_family_rank_from_user(user, family, user_klimapunkte=None):
    """1-based rank of ``user`` among the members of ``family`` by total climate points, None for non-members.

    Members with the same points share a rank. ``user_klimapunkte`` can be passed to skip recomputing it.
    """
    totals = get_klimapunkte_by_user(set(family.members.values_list("id", flat=True)))
    if user.id not in totals:
        return None
    own_total = totals[user.id] if user_klimapunkte is None else user_klimapunkte
    return 1 + sum(1 for user_id, total in totals.items() if user_id != user.id and total > own_total)


def get_worldwide_rank(user, user_klimapunkte=None):
    family = Family.objects.filter(name=WORLDWIDE_RANKING_NAME).first()
    if family is None:
        return None
    return get_family_rank_from_user(user, family, user_klimapunkte)


def get_families_of_user(user):
    return Family.objects.filter(members=user).order_by("name")


def get_communities_of_user(user):
    return Community.objects.filter(members__in=get_families_of_user(user)).distinct().order_by("name")


def get_communities_of_family(family):
    return Community.objects.filter(members=family).distinct().order_by("name")


ALLOWED_TAGS = ["p", "strong", "em", "u", "ol", "ul", "li", "a", "br", "h1", "h2"]
ALLOWED_ATTRIBUTES = {"a": ["href", "target", "rel"]}


def clean_html(html):
    cleaned = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return bleach.linkify(cleaned, callbacks=[bleach.callbacks.nofollow])


def parse_id(raw):
    """Integer id from user input, or None if it is not a plain (non-negative) integer."""
    return int(raw) if isinstance(raw, str) and raw.isdecimal() and raw.isascii() else None


def ist_email_gueltig(email):
    try:
        validate_email(email)
    except ValidationError:
        return False
    return True


def check_is_truth(request):
    if request.POST.get("is_truth") == "on":
        return True
    messages.error(request, all_messages["not_is_truth"])
    return False


def create_internal_error(request, beschreibung, fehlermeldung="interner Fehler", exception=None, throw_exception=True):
    """Log an internal error (with a redacted dump of the request) and optionally flash ``fehlermeldung``."""
    error_message = {"timestamp": timezone.now().isoformat(), "beschreibung": beschreibung}

    if request is not None:
        error_message.update(
            {
                "method": request.method,
                "path": request.path,
                "full_path": request.get_full_path(),
                "user": str(request.user) if request.user.is_authenticated else "Anonymous",
                "GET": request.GET.dict(),
                "POST": {
                    k: "***" if "password" in k.lower() or "token" in k.lower() else v
                    for k, v in request.POST.dict().items()
                },
                "COOKIES": dict.fromkeys(request.COOKIES, "***"),
                "FILES": {k: f.name for k, f in request.FILES.items()},
                # Only HTTP headers, no IP address or other sensitive fields
                "META": {k: v for k, v in request.META.items() if k.startswith("HTTP_")},
            }
        )

    if exception:
        error_message["exception"] = str(exception)
        error_message["traceback"] = traceback.format_exc()

    if throw_exception and request is not None:
        messages.error(request, fehlermeldung, fail_silently=True)  # cron jobs use requests without messages

    logger.error(error_message)

    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(settings.LOGS_DIR / "errors.log", "a", encoding="utf-8") as file:
        file.write(f"{error_message}\n\n")


def create_notification(request, notification_de, notification_en, user=None, url=None):
    if user is None:
        user = request.user
    if url is None:
        url = reverse("dashboard")

    is_german = user.usererweitert.lang == "de"
    head = "Neue Benachrichtigung" if is_german else "New notification"

    benachrichtigung = Benachrichtigung.objects.create(
        benachrichtigung_de=notification_de, benachrichtigung_en=notification_en, user=user, url=url
    )
    send_mail_function(
        request=request,
        fehlermeldung=(
            "Beim Erstellen einer Benachrichtigung ist beim Versenden der E-Mail ein Fehler aufgetreten. "
            "Die Benachrichtigung kann nur in dem Benachrichtigungsteil hier auf der Webseite gefunden werden!"
            if is_german
            else "An error occurred while sending the email during the creation of the notification. "
            "The notification can only be found in the notifications section here on the website!"
        ),
        subject="ClimateQuest - neue Benachrichtigung",
        message=notification_de if is_german else notification_en,
        recipient_list=user.email,
        user=user,
        url=url,
    )

    redirect_url = reverse("benachrichtigungen_view_focused", args=[benachrichtigung.id])
    # Push messages are plain text: drop everything from the first <span> (emoji markup) on.
    push_message = re.split(r"<span\b", notification_de if is_german else notification_en)[0]

    for token in IOSDevice.objects.filter(user=user).values_list("apns_token", flat=True):
        try:
            send_ios_push(device_token=token, title=head, body=push_message, data={"url": redirect_url})
        except Exception:  # noqa: BLE001 - a broken device token must not stop the other notifications
            logger.exception("iOS push to %s failed", user)

    if send_push(benachrichtigung=push_message, user=user, url=redirect_url, head=head) == 500:
        create_internal_error(
            request,
            "Beim Erstellen einer Benachrichtigung an das Gerät ist ein Fehler aufgetreten.",
            "Beim Erstellen einer Benachrichtigung an das Gerät ist ein Fehler aufgetreten.",
        )


def _make_jwt():
    with open(settings.APN_KEY_PATH) as f:
        key = f.read()
    return jwt.encode(
        {"iss": settings.APPLE_TEAM_ID, "iat": int(time.time())},
        key,
        algorithm="ES256",
        headers={"kid": settings.APN_KEY_ID},
    )


def send_ios_push(device_token: str, title: str, body: str, data: dict | None = None):
    payload = {"aps": {"alert": {"title": title, "body": body}, "sound": "default", "badge": 1}}
    if data:
        payload.update(data)

    with httpx.Client(http2=True, timeout=APNS_TIMEOUT_SECONDS) as client:
        response = client.post(
            f"{settings.APNS_HOST}/3/device/{device_token}",
            headers={
                "authorization": f"bearer {_make_jwt()}",
                "apns-topic": settings.APPLE_BUNDLE_ID,
                "apns-push-type": "alert",
            },
            json=payload,
        )

    if response.status_code != 200:
        raise RuntimeError(f"APNs Fehler {response.status_code}: {response.text}")


def send_push(benachrichtigung, user, url="/benachrichtigungen/", head="Neue Benachrichtigung"):
    try:
        send_user_notification(
            user=user, payload={"head": head, "body": benachrichtigung, "url": url}, ttl=PUSH_TTL_SECONDS
        )
    except TypeError:
        return 500
    return 200
