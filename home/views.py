from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Count, F, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from aktionen.models import Aktion
from artikel.models import Artikel
from community.models import Community
from core.all_messages import all_messages
from events.models import Event
from family.models import Family
from home.models import Benachrichtigung
from personals.models import TreeCodes, UserErweitert
from utils.functions import (
    KLIMAPUNKTE_PER_LIKE,
    create_notification,
    get_all_klimapunkte_from_user,
    get_hall_of_fame_entries,
    get_level,
    get_perfect_week_progress,
    get_streak_from_user,
    get_weekly_goal_from_user,
    get_worldwide_rank,
)

MAX_NOTIFICATION_LENGTH = 500
KLIMAPUNKTE_PER_KG_CO2 = 1000
PERFECT_WEEK_PERCENT = 100
HOME_STATISTICS_CACHE_KEY = "home_statistics"
HOME_STATISTICS_CACHE_SECONDS = 10 * 60


def total_klimapunkte_of_all_users():
    """Climate points of all actions, plus the bonus points and article likes of every user."""
    from_actions = Aktion.objects.aggregate(total=Sum(F("quantity") * F("aktion__klimapunkte")))["total"] or 0
    bonus = UserErweitert.objects.aggregate(total=Sum("additional_klimapunkte"))["total"] or 0
    likes = Artikel.objects.aggregate(total=Count("like"))["total"]
    return from_actions + bonus + likes * KLIMAPUNKTE_PER_LIKE


def get_home_statistics():
    """Global counters of the start page, cached for 10 minutes (they are the same for every visitor)."""
    statistics = cache.get(HOME_STATISTICS_CACHE_KEY)
    if statistics is None:
        klimapunkte_gesamt = int(total_klimapunkte_of_all_users())
        statistics = {
            "klimapunkte": klimapunkte_gesamt,
            "user_count": User.objects.count(),
            "co2": klimapunkte_gesamt // KLIMAPUNKTE_PER_KG_CO2,
            "tree_count": TreeCodes.objects.filter(planted=True).count(),
        }
        cache.set(HOME_STATISTICS_CACHE_KEY, statistics, HOME_STATISTICS_CACHE_SECONDS)
    return statistics


def home(request):
    return render(request, "./home.html", get_home_statistics())


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("home")

    user = request.user
    klimapunkte = get_all_klimapunkte_from_user(user)
    weekly_goal, weekly_klimapunkte, weekly_goal_progress_percent = get_weekly_goal_from_user(user)
    perfect_week_progress_de, perfect_week_progress_en = get_perfect_week_progress(user, timezone.localdate())
    perfect_week = weekly_goal_progress_percent >= PERFECT_WEEK_PERCENT and all(perfect_week_progress_de.values())

    return render(
        request,
        "./dashboard.html",
        {
            "weekly_goal": weekly_goal,
            "weekly_goal_progress_percent": weekly_goal_progress_percent,
            "weekly_klimapunkte": weekly_klimapunkte,
            "streak": get_streak_from_user(user),
            "perfect_week_progress_de": perfect_week_progress_de,
            "perfect_week_progress_en": perfect_week_progress_en,
            "perfect_week": perfect_week,
            "klimapunkte": klimapunkte,
            "level": get_level(user, klimapunkte)["current_level"],
            "hall_of_fame_entries": get_hall_of_fame_entries(user),
            "worldwide_ranking_rank": get_worldwide_rank(user, klimapunkte),
        },
    )


def find_notification_receivers(receiver_type, name):
    """Users addressed by the admin form, or an ``all_messages`` key describing why there are none."""
    if receiver_type == "user":
        user = User.objects.filter(username=name).first()
        return ([user], None) if user else (None, "admin__user_not_found")
    if receiver_type == "family-members":
        family = Family.objects.filter(name=name).first()
        return (family.members.all(), None) if family else (None, "admin__family_not_found")
    if receiver_type == "community-members":
        community = Community.objects.filter(name=name).first()
        if community is None:
            return None, "admin__community_not_found"
        return User.objects.filter(families__communities=community).distinct(), None
    if receiver_type == "event-participants":
        event = Event.objects.filter(id=name).first() if str(name).isdigit() else None
        return (event.participants.all(), None) if event else (None, "admin__event_not_found")
    return None, "admin__invalid_receiver_type"


@login_required
def admin(request):
    if not request.user.is_staff:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect("dashboard")
    if request.method == "POST":
        receiver = request.POST.get("receiver")
        name = request.POST.get("name")
        msg_de = request.POST.get("msg_de")
        msg_en = request.POST.get("msg_en")
        url = request.POST.get("url") or reverse("dashboard")

        if not receiver or not name or not msg_de or not msg_en:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect("admin")
        if len(msg_de) > MAX_NOTIFICATION_LENGTH or len(msg_en) > MAX_NOTIFICATION_LENGTH:
            messages.error(request, all_messages["too_long_input"])
            return redirect("admin")

        receivers, error_key = find_notification_receivers(receiver, name)
        if error_key:
            messages.error(request, all_messages[error_key])
            return redirect("admin")
        for receiving_user in receivers:
            create_notification(request, msg_de, msg_en, receiving_user, url)
        messages.success(request, all_messages["admin__successfully_sent_notification"])

    return render(request, "admin.html")


@login_required
def count_benachrichtigungen(request):
    return JsonResponse({"benachrichtigungen_count": Benachrichtigung.objects.filter(user=request.user).count()})


@login_required
def benachrichtigungen_view(request, benachrichtigungen_id=None):
    benachrichtigungen = Benachrichtigung.objects.filter(user=request.user).order_by("-date")
    return render(
        request,
        "benachrichtigungen.html",
        {"benachrichtigungen": benachrichtigungen, "benachrichtigungen_id": benachrichtigungen_id},
    )


@login_required
def delete_benachrichtigung(request, id):
    deleted, _ = Benachrichtigung.objects.filter(id=id, user=request.user).delete()
    if deleted:
        messages.success(request, all_messages["notification_deleted"])
    else:
        messages.error(request, all_messages["delete_notification_error"])
    return redirect("benachrichtigungen_view")


def nutzungsbedingungen(request):
    return render(request, "nutzungsbedingungen.html")


def datenschutz(request):
    return render(request, "datenschutz.html")


def impressum(request):
    return render(request, "impressum.html")


def companies_and_schools(request):
    return render(request, "./companies_and_schools.html")


def support(request):
    return render(request, "./support.html")


def feedback(request):
    return render(request, "./feedback.html")
