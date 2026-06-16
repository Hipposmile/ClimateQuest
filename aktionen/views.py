from datetime import datetime, timedelta, date

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import Lower
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse

from core.all_messages import all_messages
from utils.functions import dezimalstellen, get_level, get_streak_from_user, create_notification
from .models import Aktion, AktionenListe, Category, TrackedActions


def get_if_timely_action(unit):
    unit = unit.lower()
    if unit == "tag" or unit == "woche" or unit == "monat":
        return True
    return False


def get_period_start(end, quantity, unit):
    if unit == "tag":
        delta = timedelta(days=quantity)
    elif unit == "woche":
        delta = timedelta(weeks=quantity)
    elif unit == "monat":
        delta = timedelta(days=30 * quantity)
    else:
        return None

    start = end - delta
    return start


def aktion_exists_in_period(action_type, end_date, quantity, user, exclude_id=None):
    start = get_period_start(end_date, quantity, action_type.mengeBeschreibungSingular.lower())
    if start is None:
        return False

    forbidden_actions = action_type.forbidden_in_same_period.all()

    if exclude_id:
        return Aktion.objects.filter(
            user=user,
            aktion__in=[action_type, *forbidden_actions],
            date__range=(start + relativedelta(days=1), end_date)
        ).exclude(id=exclude_id).exists()
    else:
        return Aktion.objects.filter(
            user=user,
            aktion__in=[action_type, *forbidden_actions],
            date__range=(start + relativedelta(days=1), end_date)
        ).exists()


def aktion_is_in_different_action_period(action_type, end_date, user, exclude_id=None):
    forbidden_actions = action_type.forbidden_in_same_period.all()

    if exclude_id:
        actions = Aktion.objects.filter(
            user=user,
            aktion__in=[action_type, *forbidden_actions],
            date__gte=end_date,
        ).exclude(id=exclude_id).values('date', 'quantity', unit=Lower('aktion__mengeBeschreibungSingular'))
    else:
        actions = Aktion.objects.filter(
            user=user,
            aktion__in=[action_type, *forbidden_actions],
            date__gte=end_date,
        ).values('date', 'quantity', unit=Lower('aktion__mengeBeschreibungSingular'))

    for action in actions:
        start = get_period_start(action.get('date'), action.get('quantity'), action.get('unit'))
        if start is None:
            break
        if start is not None:
            start += relativedelta(days=1)
        if end_date > start:
            return True
    return False


def action_date_invalid(action_type, end_date, quantity, user, exclude_id=None):
    if aktion_exists_in_period(action_type, end_date, quantity, user, exclude_id):
        return True
    if aktion_is_in_different_action_period(action_type, end_date, user, exclude_id):
        return True
    return False


@login_required
def add(request):
    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':
        is_truth = request.POST.get('is_truth') == 'on'
        if not is_truth:
            messages.error(request, all_messages["not_is_truth"])
            return redirect('add')

        action_type_id = request.POST.get('action_type_id')
        if not action_type_id:
            messages.error(request, all_messages["action_name_missing"])
            return redirect('add')
        try:
            action = AktionenListe.objects.get(id=action_type_id)
        except AktionenListe.DoesNotExist:
            messages.error(request, all_messages["action_not_found"])
            return redirect('add')

        action_description = request.POST.get('action_description')
        if len(action_description) > 200:
            messages.error(request, all_messages["too_long_input"])
            return redirect('add')

        action_date_raw = request.POST.get('action_date')
        if not action_date_raw:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('add')
        try:
            action_date = datetime.strptime(action_date_raw, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, all_messages["invalid_date"])
            return redirect('add')

        action_quantity = request.POST.get('action_quantity')
        if not action_quantity:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('add')
        try:
            action_quantity = validate_number(action_quantity, dezimalstellen)
        except ValueError:
            messages.error(request, all_messages["action_invalid_quantity"])
            return redirect('add')
        if action_quantity <= 0 or action_quantity is False:
            messages.error(request, all_messages["invalid_quantity"])
            return redirect('add')
        elif not get_if_timely_action(action.mengeBeschreibungSingular) and (
                Aktion.objects.filter(user=request.user, aktion=action, date=action_date).aggregate(
                    total=Sum('quantity'))[
                    "total"] or 0) + action_quantity > action.max:
            messages.error(request, all_messages["max_action_quantity"])
            return redirect('add')

        action_start = get_period_start(action_date, action_quantity, action.mengeBeschreibungSingular.lower())

        if action_date > datetime.now().date():
            messages.error(request, all_messages["date_in_future"])
            return redirect('add')
        if action_start:
            if action_start < date.today() - relativedelta(months=1):
                messages.error(request, all_messages["action_too_past"])
                return redirect('add')
        else:
            if action_date < date.today() - relativedelta(months=1):
                messages.error(request, all_messages["action_too_past"])
                return redirect('add')

        if action_date_invalid(action, action_date, action_quantity, request.user):
            messages.error(request, all_messages["action_already_set_in_period"])
            return redirect('add')

        old_level = get_level(request.user)
        old_streak = get_streak_from_user(request.user)

        aktion = Aktion.objects.create(
            aktion=action,
            description=action_description,
            user=request.user,
            quantity=action_quantity,
            date=action_date,
        )

        new_level = get_level(request.user)
        new_streak = get_streak_from_user(request.user)

        if old_level['level_number'] < new_level['level_number']:
            create_notification(request,
                                f'Du hast eine neue Aktion vom Typen {action.name} erstellt und bist so ins Level {new_level["current_level"].description} aufgestiegen. <span class="emoji">&#x1F973;</span>',
                                f'You created a action (type: {action.name_en}) and so reached the level {new_level["current_level"].description_en}. <span class="emoji">&#x1F973;</span>',
                                request.user,
                                reverse('level_me'))
            if request.LANGUAGE_CODE == "de":
                messages.success(request,
                                 f'Du hast eine neue Aktion vom Typen {action.name} erstellt und bist so ins Level {new_level["current_level"].description} aufgestiegen. <span class="emoji">&#x1F973;')
            else:
                messages.success(request,
                                 f'You created a action (type: {action.name_en}) and so reached the level {new_level["current_level"].description_en}. <span class="emoji">&#x1F973;</span>')
            messages.info(request, "request-review")
        if old_streak < new_streak:
            create_notification(request,
                                f'Du hast eine neue Aktion vom Typen {action.name} erstellt und so deine Streak verlängert. <span class="emoji">&#x1F973;</span>',
                                f'You created a new action (type: {action.name_en}) and so extended your streak. <span class="emoji">&#x1F973;</span>',
                                request.user,
                                reverse('dashboard'))
            if request.LANGUAGE_CODE == "de":
                messages.success(request,
                                 f'Du hast eine neue Aktion vom Typen {action.name} erstellt und deine Streak verlängert. <span class="emoji">&#x1F973;</span>')
            else:
                messages.success(request,
                                 f'You created a new action (type: {action.name_en}) and so extended your streak. <span class="emoji">&#x1F973;</span>')
        messages.success(request, all_messages["action_added"])
        return redirect('action_detail', aktion.id, request.user.id)

    return render(request, './add.html', {'categories': categories})


@login_required
def track_actions(request):
    trackable_actions_weekly = AktionenListe.objects.filter(track_weekly=True).order_by('name')
    trackable_actions_weekly_with_done = {}
    for action in trackable_actions_weekly:
        tracked_action = TrackedActions.objects.filter(action=action, user=request.user).first()
        trackable_actions_weekly_with_done[action.name] = {
            'action': action,
            'done': tracked_action is not None,
            'since': tracked_action.since if tracked_action else None,
        }

    trackable_actions_kilometerly = AktionenListe.objects.filter(track_kilometerly=True).order_by('name')

    if request.method == 'POST':
        if 'weekly_track' in request.POST:
            action_id = request.POST.get('weekly_track')
            try:
                action = AktionenListe.objects.get(id=action_id)
            except AktionenListe.DoesNotExist:
                messages.error(request, all_messages["internal_error"])
                return redirect('track_actions')

            if TrackedActions.objects.filter(action=action, user=request.user).exists():
                TrackedActions.objects.filter(action=action, user=request.user).delete()
                messages.success(request, all_messages["stopped_tracking"])
                return redirect('track_actions')
            else:
                forbidden_in_same_period = action.forbidden_in_same_period.all()
                if TrackedActions.objects.filter(action__in=forbidden_in_same_period, user=request.user).exists():
                    messages.error(request, all_messages["forbidden_tracking_action"])
                    return redirect('track_actions')
                TrackedActions.objects.create(action=action, user=request.user)
                messages.success(request, all_messages["tracking_action"])
                return redirect('track_actions')

        if 'kilometerly_track' in request.POST:
            distance = request.POST.get('distance')

            try:
                distance = int(distance)
            except ValueError:
                messages.error(request, all_messages["internal_error"])
                return redirect('track_actions')

            action_id = request.POST.get('action_id')

            try:
                action = AktionenListe.objects.get(id=action_id)
            except AktionenListe.DoesNotExist:
                return JsonResponse({'success': False, 'error': all_messages["internal_error"]})

            action = Aktion.objects.create(aktion=action, user=request.user, quantity=(distance / 1000),
                                           date=date.today(),
                                           description='Diese Aktion wurde vom ClimateQuest Tracking Service automatisch getrackt.' if request.user.usererweitert.lang == "de" else 'This action was automatically tracked by the ClimateQuest Tracking Service.')

            return JsonResponse({'success': True, 'action_id': action.id, 'user_id': request.user.id})

    return render(request, './track.html', {'trackable_actions_weekly': trackable_actions_weekly_with_done,
                                            'trackable_actions_kilometerly': trackable_actions_kilometerly})


def add_weekly_tracking_action():
    all_actions = TrackedActions.objects.all()

    for tracked_action in all_actions:
        user = tracked_action.user
        action = tracked_action.action
        today = date.today()

        if (today - tracked_action.since).days >= 6 and not action_date_invalid(action, today, 1, user):
            Aktion.objects.create(user=user, aktion=action, quantity=1, date=today,
                                  description="Eingetragen vom ClimateQuest Tracking Service" if user.usererweitert.lang == "de" else "This action was added by the ClimateQuest Tracking Service.")


def validate_number(number, input_decimals):
    if not number:
        return False
    try:
        number = float(number)
    except ValueError:
        number = number.replace(",", ".")
        try:
            number = float(number)
        except ValueError:
            return False
    return round(number, input_decimals)
