from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from core.all_messages import all_messages
from utils.action_feedback import report_action_change
from utils.functions import get_level, get_streak_from_user, parse_id

from .models import Aktion, AktionenListe, Category, TrackedActions
from .services import ActionInputError, action_date_invalid, validate_action_input

METERS_PER_KILOMETER = 1000
TRACKING_DESCRIPTION_DE = "Diese Aktion wurde vom ClimateQuest Tracking Service automatisch getrackt."
TRACKING_DESCRIPTION_EN = "This action was automatically tracked by the ClimateQuest Tracking Service."
WEEKLY_TRACKING_DESCRIPTION_DE = "Eingetragen vom ClimateQuest Tracking Service"
WEEKLY_TRACKING_DESCRIPTION_EN = "This action was added by the ClimateQuest Tracking Service."
WEEKLY_TRACKING_INTERVAL_DAYS = 6


@login_required
def add(request):
    if request.method == "POST":
        try:
            validated = validate_action_input(request.user, request.POST)
        except ActionInputError as error:
            messages.error(request, error.message)
            return redirect("add")

        old = (get_level(request.user), get_streak_from_user(request.user))
        aktion = Aktion.objects.create(
            aktion=validated.action_type,
            description=validated.description,
            user=request.user,
            quantity=validated.quantity,
            date=validated.date,
        )
        new = (get_level(request.user), get_streak_from_user(request.user))
        report_action_change(request, "created", validated.action_type, old, new)
        messages.success(request, all_messages["action_added"])
        return redirect("action_detail", aktion.id, request.user.id)

    return render(request, "./add.html", {"categories": Category.objects.order_by("name")})


def _toggle_weekly_tracking(request):
    action = AktionenListe.objects.filter(id=parse_id(request.POST.get("weekly_track"))).first()
    if action is None:
        messages.error(request, all_messages["internal_error"])
        return

    tracked, _ = TrackedActions.objects.filter(action=action, user=request.user).delete()
    if tracked:
        messages.success(request, all_messages["stopped_tracking"])
    elif TrackedActions.objects.filter(
        action__in=action.forbidden_in_same_period.all(), user=request.user
    ).exists():
        messages.error(request, all_messages["forbidden_tracking_action"])
    else:
        TrackedActions.objects.create(action=action, user=request.user)
        messages.success(request, all_messages["tracking_action"])


def _track_kilometers(request):
    """AJAX endpoint of the distance tracker: records the driven distance (in meters) as an action."""
    try:
        distance = int(request.POST.get("distance"))
    except (TypeError, ValueError):
        distance = 0
    if distance <= 0:
        messages.error(request, all_messages["internal_error"])
        return redirect("track_actions")

    action_type = AktionenListe.objects.filter(
        id=parse_id(request.POST.get("action_id")), track_kilometerly=True,
    ).first()
    if action_type is None:
        return JsonResponse({"success": False, "error": str(all_messages["internal_error"])})

    aktion = Aktion.objects.create(
        aktion=action_type,
        user=request.user,
        quantity=distance / METERS_PER_KILOMETER,
        date=timezone.localdate(),
        description=TRACKING_DESCRIPTION_DE if request.user.usererweitert.lang == "de" else TRACKING_DESCRIPTION_EN,
    )
    return JsonResponse({"success": True, "action_id": aktion.id, "user_id": request.user.id})


@login_required
def track_actions(request):
    if request.method == "POST":
        if "weekly_track" in request.POST:
            _toggle_weekly_tracking(request)
            return redirect("track_actions")
        if "kilometerly_track" in request.POST:
            return _track_kilometers(request)

    tracked_since = dict(TrackedActions.objects.filter(user=request.user).values_list("action_id", "since"))
    weekly_actions = {
        action.name: {
            "action": action,
            "done": action.id in tracked_since,
            "since": tracked_since.get(action.id),
        }
        for action in AktionenListe.objects.filter(track_weekly=True).order_by("name")
    }
    return render(
        request,
        "./track.html",
        {
            "trackable_actions_weekly": weekly_actions,
            "trackable_actions_kilometerly": AktionenListe.objects.filter(track_kilometerly=True).order_by("name"),
        },
    )


def add_weekly_tracking_action():
    """Cron job: add one action per week for every action a user tracks weekly."""
    today = timezone.localdate()
    for tracked in TrackedActions.objects.select_related("user__usererweitert", "action"):
        if (today - tracked.since).days < WEEKLY_TRACKING_INTERVAL_DAYS:
            continue
        if action_date_invalid(tracked.action, today, 1, tracked.user):
            continue
        is_german = tracked.user.usererweitert.lang == "de"
        Aktion.objects.create(
            user=tracked.user,
            aktion=tracked.action,
            quantity=1,
            date=today,
            description=WEEKLY_TRACKING_DESCRIPTION_DE if is_german else WEEKLY_TRACKING_DESCRIPTION_EN,
        )
