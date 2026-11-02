import math
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from core.all_messages import all_messages
from utils.functions import clean_html, create_notification, parse_id

from .models import Answer, Event, Question

MAX_TEXT_LENGTH = 100
FORM_DATETIME_FORMAT = "%Y-%m-%dT%H:%M"
ORDER_FIELDS = {
    "Name": "name",
    "Datum": "date_time",
    "Dauer": "duration",
    "Adresse": "adress",
    "Ersteller": "creator__username",
}


def events_overview(request):
    ordered_by, search_keyword, past_events_visible = "Name", None, False
    events = Event.objects.select_related("creator").prefetch_related("participants")

    if request.method == "POST":
        ordered_by = request.POST.get("order_by")
        search_keyword = request.POST.get("search_keyword")
        past_events_visible = request.POST.get("past_events_visible") == "on"
        if not past_events_visible:
            events = events.filter(date_time__gte=timezone.now())
        user = request.user if request.user.is_authenticated else None

        if ordered_by == "Teilnehmeranzahl":
            events = events.annotate(num_participants=Count("participants", distinct=True))
            if search_keyword:
                try:
                    search_keyword = int(search_keyword)
                except ValueError:
                    messages.error(request, all_messages["teilnehmeranzahl_search_keyword_not_a_number"])
                    return redirect("events_overview")
                events = events.filter(num_participants__icontains=search_keyword)
            events = events.order_by("-num_participants", "pk")
        elif ordered_by == "von mir erstellte Events":
            events = (events.filter(creator=user) if user else events.none()).order_by("name", "pk")
        elif ordered_by == "Events, bei denen ich Teilnehmer bin":
            events = (events.filter(participants=user) if user else events.none()).order_by("name", "pk")
        else:
            order_by = ORDER_FIELDS.get(ordered_by, "name")
            if search_keyword:
                events = events.filter(**{f"{order_by}__icontains": search_keyword})
            events = events.order_by(order_by, "pk")
    else:
        events = events.filter(date_time__gte=timezone.now()).order_by("name", "pk")

    return render(
        request,
        "./events_overview.html",
        {
            "ordered_by": ordered_by,
            "search_keyword": search_keyword,
            "past_events_visible": past_events_visible,
            "events": events,
        },
    )


def _toggle_participation(request, event):
    if request.user == event.creator:
        messages.success(request, all_messages["event__user_is_creator"])
    elif event.participants.filter(id=request.user.id).exists():
        event.participants.remove(request.user)
        messages.success(request, all_messages["left_event"])
    else:
        event.participants.add(request.user)
        messages.success(request, all_messages["joined_event"])


def _ask_question(request, event):
    text = (request.POST.get("question") or "").strip()
    if not text:
        messages.error(request, all_messages["missing_required_inputs"])
        return
    event.questions.add(Question.objects.create(question=text, user=request.user))
    messages.success(request, all_messages["successfully_asked_question"])


def _answer_question(request, event):
    question = event.questions.filter(id=parse_id(request.POST.get("question_id"))).first()
    if question is None:
        messages.error(request, all_messages["internal_error"])
        return
    text = (request.POST.get("answer") or "").strip()
    if not text:
        messages.error(request, all_messages["missing_required_inputs"])
        return
    question.answers.add(Answer.objects.create(answer=text, user=request.user))
    messages.success(request, all_messages["successfully_answered_question"])


EVENT_ACTIONS = {
    "become_member": _toggle_participation,
    "ask_question": _ask_question,
    "answer_question": _answer_question,
}


def event_detail(request, event_id):
    event = (
        Event.objects.select_related("creator")
        .prefetch_related("participants", "questions__user", "questions__answers__user")
        .filter(id=event_id)
        .first()
    )
    if event is None:
        messages.error(request, all_messages["event_not_existing"])
        return redirect("events_overview")

    if request.method == "POST" and request.user.is_authenticated:
        for button, handler in EVENT_ACTIONS.items():
            if button in request.POST:
                handler(request, event)
                return redirect("event_detail", event_id)
    return render(request, "./event_detail.html", {"event": event})


def read_event_form(request, description_field):
    """Validated values of the add/edit event form as a dict, or None after flashing the problem."""
    post = request.POST
    if post.get("is_truth") != "on":
        messages.error(request, all_messages["not_is_truth"])
        return None
    name = post.get("name") or ""
    description = post.get(description_field) or ""
    raw_date_time = post.get("date_time") or ""
    raw_duration = post.get("duration") or ""
    adress = post.get("adress") or ""
    if not (name and description and raw_date_time and raw_duration and adress):
        messages.error(request, all_messages["missing_required_inputs"])
        return None
    if len(name) > MAX_TEXT_LENGTH or len(adress) > MAX_TEXT_LENGTH:
        messages.error(request, all_messages["too_long_input"])
        return None
    try:
        date_time = timezone.make_aware(datetime.strptime(raw_date_time, FORM_DATETIME_FORMAT))
    except ValueError:
        messages.error(request, all_messages["invalid_date"])
        return None
    if date_time < timezone.now() + timedelta(days=1):
        messages.error(request, all_messages["date_must_be_tomorrow"])
        return None
    try:
        duration = float(raw_duration.replace(",", "."))
    except ValueError:
        duration = math.nan
    if not math.isfinite(duration) or duration < 0:
        messages.error(request, all_messages["invalid_duration"])
        return None
    return {
        "name": name,
        "description": clean_html(description),
        "date_time": date_time,
        "duration": duration,
        "adress": adress,
    }


@login_required
def add_event(request):
    if request.method == "POST":
        values = read_event_form(request, "content")
        if values is None:
            return redirect("add_event")
        event = Event.objects.create(creator=request.user, **values)
        messages.success(request, all_messages["successfully_created_event"])
        return redirect("event_detail", event.id)
    return render(request, "./add_event.html")


def _notify_participants(request, event, text_de, text_en, url):
    for participant in event.participants.all():
        create_notification(request, text_de, text_en, participant, url=url)


@login_required
def edit_event(request, event_id):
    event = Event.objects.filter(id=event_id).first()
    if event is None:
        messages.error(request, all_messages["event_not_existing"])
        return redirect("events_overview")
    if request.user != event.creator:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect("events_overview")

    if request.method == "POST":
        if "edit" in request.POST:
            values = read_event_form(request, "content")
            if values is None:
                return redirect("edit_event", event_id)
            for field, value in values.items():
                setattr(event, field, value)
            event.save()
            _notify_participants(
                request,
                event,
                f"Ein Event, bei dem du Teilnehmer bist und das jetzt {event.name} heißt, wurde bearbeitet.",
                f"An event you are participating in and that is now called {event.name} has been edited.",
                reverse("event_detail", args=[event_id]),
            )
            messages.success(request, all_messages["successfully_edited_event"])
            return redirect("event_detail", event_id)
        if "delete" in request.POST:
            _notify_participants(
                request,
                event,
                f"Das Event {event.name}, bei dem du Teilnehmer bist, wurde gelöscht",
                f"The event called {event.name} has been deleted.",
                reverse("events_overview"),
            )
            event.delete()
            messages.success(request, all_messages["successfully_deleted_event"])
            return redirect("events_overview")
        messages.error(request, all_messages["internal_error"])
    return render(request, "./edit_event.html", {"event": event})
