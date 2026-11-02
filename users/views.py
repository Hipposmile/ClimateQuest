from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.html import escape

from aktionen.models import Aktion, Category
from aktionen.services import ActionInputError, validate_action_input
from core.all_messages import all_messages
from home.models import ReportedUser
from utils.action_feedback import report_action_change
from utils.functions import (
    get_additional_klimapunkte,
    get_all_klimapunkte_from_user,
    get_hall_of_fame_entries,
    get_klimapunkte_for_member,
    get_level,
    get_streak_from_user,
    get_weekly_goal_from_user,
    get_worldwide_rank,
    send_mail_function,
)
from utils.periods import InvalidPeriod, default_period, parse_period

KLIMAPUNKTE_PER_KG_CO2 = 1000
REPORT_RECEIVER_USERNAME = "admin"


def get_user(request, user_id, allow_needed=True):
    """The user with ``user_id`` if the requester may see their data, otherwise False (with a flash message)."""
    user = User.objects.select_related("usererweitert").filter(id=user_id).first()
    if user is None:
        messages.error(request, all_messages["user_not_found"])
        return False
    if allow_needed and user != request.user and not getattr(user.usererweitert, "allows_data_view", False):
        messages.error(request, all_messages["user_blocked_view"])
        return False
    return user


@login_required
def klimapunkte_view(request, user_id):
    user = get_user(request, user_id)
    if not user:
        return redirect("user_detail", user_id)

    period = default_period()
    if request.method == "POST":
        try:
            period = parse_period(request.POST, request.LANGUAGE_CODE, timezone.localdate())
        except InvalidPeriod as error:
            messages.error(request, error.message)
            return redirect("klimapunkte_view", user_id)

    additional_klimapunkte = get_additional_klimapunkte(user)
    klimapunkte = get_klimapunkte_for_member(user, period.start, period.end)
    return render(
        request,
        "./klimapunkte.html",
        {
            "klimapunkte": klimapunkte,
            "additional_klimapunkte": additional_klimapunkte,
            "klimapunkte_total": klimapunkte + additional_klimapunkte,
            "saved_co2": klimapunkte / KLIMAPUNKTE_PER_KG_CO2,
            "zeitraum": period.text,
            "user": user,
        },
    )


def level_view(request, user_id):
    user = get_user(request, user_id)
    if not user:
        return redirect("user_detail", user_id)
    return render(request, "./level.html", {"level_data": get_level(user), "user": user})


def history(request, user_id):
    user = get_user(request, user_id)
    if not user:
        return redirect("user_detail", user_id)
    actions = Aktion.objects.filter(user=user).select_related("aktion").order_by("-date", "-id")
    return render(request, "./history.html", {"actions": actions, "user": user})


def users_overview(request):
    if request.method == "POST":
        search_keyword = request.POST.get("search_keyword") or ""
        users = User.objects.filter(username__icontains=search_keyword).order_by("username")
        return render(request, "users_overview.html", {"users": users, "search_keyword": search_keyword})
    return render(request, "users_overview.html")


def user_detail(request, user_id):
    user = get_user(request, user_id, False)
    if not user:
        return redirect("dashboard")

    if request.user.is_authenticated and request.method == "POST":
        reason = (request.POST.get("reason") or "").strip()
        if reason:
            report_user(request, user, request.user, reason)
            messages.success(request, all_messages["reported_user"])
        else:
            messages.error(request, all_messages["missing_required_inputs"])

    klimapunkte = get_all_klimapunkte_from_user(user)
    weekly_goal, weekly_klimapunkte, weekly_goal_progress_percent = get_weekly_goal_from_user(user)
    return render(
        request,
        "./user_detail.html",
        {
            "user_expanded": user.usererweitert,
            "weekly_goal": weekly_goal,
            "weekly_goal_progress_percent": weekly_goal_progress_percent,
            "weekly_klimapunkte": weekly_klimapunkte,
            "streak": get_streak_from_user(user),
            "all_klimapunkte": klimapunkte,
            "worldwide_ranking_rank": get_worldwide_rank(user, klimapunkte),
            "hall_of_fame_entries": get_hall_of_fame_entries(user),
        },
    )


def _snapshot(user):
    return get_level(user), get_streak_from_user(user)


def _edit_action(request, current_action):
    try:
        validated = validate_action_input(
            request.user, request.POST, action_date=current_action.date, exclude_id=current_action.id
        )
    except ActionInputError as error:
        messages.error(request, error.message)
        return

    old = _snapshot(request.user)
    current_action.aktion = validated.action_type
    current_action.description = validated.description
    current_action.quantity = validated.quantity
    current_action.save()
    report_action_change(request, "edited", validated.action_type, old, _snapshot(request.user))
    messages.success(request, all_messages["action_edited"])


def _delete_action(request, current_action):
    old = _snapshot(request.user)
    action_type = current_action.aktion
    current_action.delete()
    report_action_change(request, "deleted", action_type, old, _snapshot(request.user))
    messages.success(request, all_messages["action_deleted"])


def action_detail(request, action_id, user_id):
    user = get_user(request, user_id)
    if not user:
        return redirect("user_detail", user_id)

    current_action = Aktion.objects.select_related("aktion").filter(id=action_id, user=user).first()
    if current_action is None:
        messages.error(request, all_messages["action_not_found"])
        return redirect("history_me")

    if request.user == user and request.method == "POST":
        if "edit_action" in request.POST:
            _edit_action(request, current_action)
            return redirect("action_detail", action_id, user_id)
        if "delete_action" in request.POST:
            _delete_action(request, current_action)
            return redirect("history_me")

    return render(
        request,
        "./action_detail.html",
        {"categories": Category.objects.order_by("name"), "current_action": current_action, "user": user},
    )


@login_required
def klimapunkte_me(request):
    return redirect("klimapunkte_view", request.user.id)


@login_required
def level_me(request):
    return redirect("level_view", request.user.id)


@login_required
def history_me(request):
    return redirect("history", request.user.id)


def report_user(request, reported_user, reporting_user, reason):
    """Store a report about ``reported_user`` and mail it to the site administrator."""
    report = ReportedUser.objects.create(reported_user=reported_user, reporting_user=reporting_user, reason=reason)
    receiver = User.objects.filter(is_superuser=True, is_staff=True, username=REPORT_RECEIVER_USERNAME).first()
    if receiver is None:
        return report
    send_mail_function(
        request=request,
        subject=f"User {reported_user.username} wurde von {reporting_user.username} gemeldet",
        message=f"""
            <h2>Gemeldeter User</h2>
            <p>Username: {escape(reported_user.username)}</p>
            <p>ID: {reported_user.id}</p>
            <h2>Meldender User</h2>
            <p>Username: {escape(reporting_user.username)}</p>
            <p>ID: {reporting_user.id}</p>
            <h2>Begründung</h2>
            <p>{escape(reason)}</p>
        """,
        user=receiver,
        url=f"/ClimateQuestAdmin/home/reporteduser/{report.id}/change/",
    )
    return report

