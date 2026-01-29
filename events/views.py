from django.db.models import Count
from django.shortcuts import render, redirect

from core.all_messages import all_messages
from utils.functions import *
from .models import *
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta


def events_overview(request):
    if request.method == 'POST':
        already_ordered = False

        ordered_by = request.POST.get('order_by')
        search_keyword = request.POST.get('search_keyword')
        past_events_visible = request.POST.get('past_events_visible') == 'on'

        if past_events_visible:
            all_events = Event.objects.all()
        else:
            all_events = Event.objects.filter(date_time__gte=timezone.now())

        order_map = {
            "Name": "name",
            "Datum": "date_time",
            "Dauer": "duration",
            "Adresse": "adress",
            "Ersteller": "creator__username"
        }
        order_by = order_map.get(ordered_by, "name")

        if ordered_by == "Teilnehmeranzahl":
            if search_keyword:
                try:
                    search_keyword = int(search_keyword)
                except ValueError:
                    messages.error(request, all_messages["teilnehmeranzahl_search_keyword_not_a_number"])
                    return redirect('events_overview')

            events = all_events.annotate(num_participants=Count('participants'))
            if search_keyword:
                events = events.filter(num_participants__icontains=search_keyword)
            events = events.order_by('-num_participants')
            already_ordered = True

        elif ordered_by == "von mir erstellte Events":
            if request.user.is_authenticated:
                events = all_events.filter(creator=request.user)
                already_ordered = True

        elif ordered_by == "Events, bei denen ich Teilnehmer bin":
            if request.user.is_authenticated:
                events = all_events.filter(participants=request.user)
                already_ordered = True

        if not already_ordered:
            if search_keyword:
                events = all_events.filter(**{f"{order_by}__icontains": search_keyword})
            else:
                events = all_events
            events = events.order_by(order_by)

    else:
        ordered_by = "Name"
        search_keyword = None
        past_events_visible = False
        events = Event.objects.filter(date_time__gte=timezone.now()).order_by("name")

    return render(request, './events_overview.html', {
        'ordered_by': ordered_by,
        'search_keyword': search_keyword,
        'past_events_visible': past_events_visible,
        'events': events
    })


def event_detail(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        messages.error(request, all_messages["event_not_existing"])
        return redirect('events_overview')

    if request.method == 'POST':
        if 'become_member' in request.POST:
            if request.user == event.creator:
                messages.success(request, all_messages["event__user_is_creator"])
            elif request.user in event.participants.all():
                event.participants.remove(request.user)
                messages.success(request, all_messages["left_event"])
            else:
                event.participants.add(request.user)
                messages.success(request, all_messages["joined_event"])

            return redirect('event_detail', event_id)

        elif 'ask_question' in request.POST:
            question_text = request.POST.get('question')
            question = Question.objects.create(question=question_text, user=request.user)
            event.questions.add(question)

            messages.success(request, all_messages["successfully_asked_question"])
            return redirect('event_detail', event_id)

        elif 'answer_question' in request.POST:
            question_id = request.POST.get('question_id')
            try:
                question = Question.objects.get(id=question_id)
            except Question.DoesNotExist:
                messages.error(request, all_messages["internal_error"])
                return redirect('events_overview')

            answer_text = request.POST.get('answer')

            answer = Answer.objects.create(answer=answer_text, user=request.user)
            question.answers.add(answer)

            messages.success(request, all_messages["successfully_answered_question"])
            return redirect('event_detail', event_id)

    return render(request, './event_detail.html', {'event': event})


@login_required
def add_event(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        content = request.POST.get('content')
        date_time = request.POST.get('date_time')
        duration = request.POST.get('duration')
        adress = request.POST.get('adress')

        is_truth = request.POST.get('is_truth') == 'on'
        if not is_truth:
            messages.error(request, all_messages["not_is_truth"])
            return redirect('add_event')

        if len(name) > 100 or len(adress) > 100:
            messages.error(request, all_messages["too_long_input"])
            return redirect('add_event')

        if not name or not content or not date_time or not duration or not adress:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('add_event')

        content = clean_html(content)

        try:
            date_time = datetime.strptime(date_time, '%Y-%m-%dT%H:%M')
            date_time = timezone.make_aware(date_time)
        except ValueError:
            messages.error(request, all_messages["invalid_date"])
            return redirect('add_event')

        tomorrow = timezone.now() + timedelta(days=1)

        if date_time < tomorrow:
            messages.error(request, all_messages["date_must_be_tomorrow"])
            return redirect('add_event')

        Event.objects.create(
            name=name,
            description=content,
            adress=adress,
            date_time=date_time,
            duration=duration,
            creator=request.user
        )

        messages.success(request, all_messages["successfully_created_event"])
        return redirect('events_overview')

    return render(request, './add_event.html')


@login_required
def edit_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        messages.error(request, all_messages["event_not_existing"])

    if request.user != event.creator:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect('events_overview')

    if request.method == 'POST':
        if 'edit' in request.POST:
            name = request.POST.get('name')
            description = request.POST.get('description')
            date_time = request.POST.get('date_time')
            duration = request.POST.get('duration')
            adress = request.POST.get('adress')

            is_truth = request.POST.get('is_truth') == 'on'
            if not is_truth:
                messages.error(request, all_messages["not_is_truth"])
                return redirect('edit_event', event_id)

            if len(name) > 100 or len(adress) > 100:
                messages.error(request, all_messages["too_long_input"])
                return redirect('edit_event', event_id)

            if not name or not description or not date_time or not duration or not adress:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('edit_event', event_id)

            description = clean_html(description)

            try:
                date_time = datetime.strptime(date_time, '%Y-%m-%dT%H:%M')
                date_time = timezone.make_aware(date_time)
            except ValueError:
                messages.error(request, all_messages["invalid_date"])
                return redirect('edit_event', event_id)

            tomorrow = timezone.now() + timedelta(days=1)

            if date_time < tomorrow:
                messages.error(request, all_messages["date_must_be_tomorrow"])
                return redirect('edit_event', event_id)

            event.name = name
            event.description = description
            event.date_time = date_time
            event.duration = duration
            event.adress = adress
            event.save()

            for participant in event.participants.all():
                create_notification(request,
                                    f'Ein Event, bei dem du Teilnehmer bist und das jetzt {name} heißt, wurde bearbeitet.',
                                    participant)

            messages.success(request, all_messages["successfully_edited_event"])
            return redirect('event_detail', event_id)

        elif 'delete' in request.POST:
            for participant in event.participants.all():
                create_notification(request, f'Das Event {event.name}, bei dem du Teilnehmer bist, wurde gelöscht',
                                    participant)
            event.delete()
            messages.success(request, all_messages["successfully_deleted_event"])
            return redirect('events_overview')

        else:
            messages.success(request, all_messages["internal_error"])

    return render(request, './edit_event.html', {'event': event})
