from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from core.all_messages import all_messages
from utils.functions import *


@login_required
def add(request):
    aktionen = AktionenListe.objects.all().order_by('name')
    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':
        is_truth = request.POST.get('is_truth') == 'on'
        if not is_truth:
            messages.error(request, all_messages["not_is_truth"])
            return redirect('add')

        action_type = request.POST.get('action_type')
        if not action_type:
            messages.error(request, all_messages["action_name_missing"])
            return redirect('add')

        try:
            action = AktionenListe.objects.get(name=action_type)
        except AktionenListe.DoesNotExist:
            messages.error(request, all_messages["action_not_found"])

        action_description = request.POST.get('action_description')
        if len(action_description) > 200:
            messages.error(request, all_messages["too_long_input"])

        action_date_raw = request.POST.get('action_date')
        if not action_date_raw:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('add')
        try:
            action_date = datetime.strptime(action_date_raw, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, all_messages["invalid_date"])
            return redirect('add')
        if action_date > datetime.now().date():
            messages.error(request, all_messages["date_in_future"])
            return redirect('add')
        elif action_date < date.today() - relativedelta(years=100):
            messages.error(request, all_messages["action_too_past"])
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
        if action_quantity < 0 or action_quantity is False:
            messages.error(request, all_messages["invalid_quantity"])
            return redirect('add')
        elif (Aktion.objects.filter(user=request.user, aktion=action).aggregate(total=Sum('quantity'))[
                  "total"] or 0) + action_quantity > action.max:
            messages.error(request, all_messages["max_action_quantity"])
            return redirect('add')

        aktion_existing = any(aktion.name == action_type for aktion in aktionen)
        if not aktion_existing:
            messages.error(request, all_messages["invalid_action_type"])
            return redirect('add')

        old_level = get_level(request.user)
        old_weekly_goal_progress_percent = get_weekly_goal_from_user(request.user)[-1]
        old_streak = get_streak_from_user(request.user)

        Aktion.objects.create(
            aktion=action,
            description=action_description,
            user=request.user,
            quantity=action_quantity,
            date=action_date,
        )

        new_level = get_level(request.user)
        new_weekly_goal_progress_percent = get_weekly_goal_from_user(request.user)[-1]
        new_streak = get_streak_from_user(request.user)

        if old_level['level_number'] < new_level['level_number']:
            create_notification(request,
                                f'Du hast eine neue Aktion vom Typen {action_type} erstellt und bist so ins Level {new_level["current_level"].description} aufgestiegen. <span class="emoji">&#x1F973;</span>',
                                request.user)
        if new_weekly_goal_progress_percent >= 100 > old_weekly_goal_progress_percent:
            create_notification(request,
                                f'Du hast eine neue Aktion vom Typen {action_type} erstellt und so dein wöchentliches Ziel erreicht. <span class="emoji">&#x1F973;</span>',
                                request.user
                                )
        if old_streak < new_streak:
            create_notification(request,
                                f'Du hast eine neue Aktion vom Typen {action_type} erstellt und so deine Streak verlängert. <span class="emoji">&#x1F973;</span>',
                                request.user)
        messages.success(request, all_messages["action_added"])
        return redirect('history')

    return render(request, './add.html', {'categories': categories})


@login_required
def edit_action(request, action_id):
    if not action_id:
        messages.error(request, all_messages["action_id_missing"])
        return redirect('history')
    try:
        current_action = Aktion.objects.get(id=action_id, user=request.user)
    except Aktion.DoesNotExist:
        messages.error(request, all_messages["action_not_found"])
        return redirect('history')

    aktionen = AktionenListe.objects.all().order_by('name')
    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':
        if 'edit_action' in request.POST:
            is_truth = request.POST.get('is_truth') == 'on'
            if not is_truth:
                messages.error(request, all_messages["not_is_truth"])
                return redirect('edit_action', action_id=action_id)

            action_type = request.POST.get('action_type')
            if not action_type:
                messages.error(request, all_messages["action_name_missing"])
                return redirect('edit_action', action_id)

            try:
                action = AktionenListe.objects.get(name=action_type)
            except AktionenListe.DoesNotExist:
                messages.error(request, all_messages["action_not_found"])

            action_description = request.POST.get('action_description')
            if len(action_description) > 200:
                messages.error(request, all_messages["too_long_input"])

            action_date_raw = request.POST.get('action_date')
            if not action_date_raw:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('edit_action', action_id)
            try:
                action_date = datetime.strptime(action_date_raw, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, all_messages["invalid_date"])
                return redirect('edit_action', action_id)
            if action_date > datetime.now().date():
                messages.error(request, all_messages["date_in_future"])
                return redirect('edit_action', action_id)
            elif action_date < date.today() - relativedelta(years=100):
                messages.error(request, all_messages["action_too_past"])
                return redirect('edit_action', action_id)

            action_quantity = request.POST.get('action_quantity')
            if not action_quantity:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('edit_action', action_id)
            try:
                action_quantity = validate_number(action_quantity, dezimalstellen)
            except ValueError:
                messages.error(request, all_messages["action_invalid_quantity"])
                return redirect('edit_action', action_id)
            if action_quantity < 0 or action_quantity is False:
                messages.error(request, all_messages["invalid_quantity"])
                return redirect('edit_action', action_id)
            elif (Aktion.objects.filter(user=request.user, aktion=action).aggregate(total=Sum('quantity'))[
                      "total"] or 0) + action_quantity > action.max:
                messages.error(request, all_messages["max_action_quantity"])
                return redirect('edit_action', action_id)

            action_existing = any(aktion.name == action_type for aktion in aktionen)
            if not action_existing:
                messages.error(request, all_messages["invalid_action_type"])
                return redirect('edit_action', action_id)

            old_level = get_level(request.user)
            old_weekly_goal_progress_percent = get_weekly_goal_from_user(request.user)[-1]
            old_streak = get_streak_from_user(request.user)

            current_action.aktion = action
            current_action.description = action_description
            current_action.user = request.user
            current_action.quantity = action_quantity
            current_action.date = action_date
            current_action.save()

            new_level = get_level(request.user)
            new_weekly_goal_progress_percent = get_weekly_goal_from_user(request.user)[-1]
            new_streak = get_streak_from_user(request.user)

            if old_level['level_number'] < new_level['level_number']:
                create_notification(request,
                                    f'Du hast eine Aktion vom Typen {action_type} bearbeitet und bist so ins Level {new_level["current_level"].description} aufgestiegen. <span class="emoji">&#x1F973;</span>',
                                    request.user)
            elif old_level['level_number'] > new_level['level_number']:
                create_notification(request,
                                    f'Du hast eine Aktion vom Typen {action_type} bearbeitet, dadurch Klimapunkte verloren und bist so ins Level {new_level["current_level"].description} abgestiegen. <span class="emoji">&#x1F622;</span>',
                                    request.user)
            if new_weekly_goal_progress_percent >= 100 > old_weekly_goal_progress_percent:
                create_notification(request,
                                    f'Du hast eine neue Aktion vom Typen {action_type} bearbeitet und so dein wöchentliches Ziel erreicht. <span class="emoji">&#x1F973;</span>',
                                    request.user
                                    )
            elif new_weekly_goal_progress_percent < 100 <= old_weekly_goal_progress_percent:
                create_notification(request,
                                    f'Du hast eine neue Aktion vom Typen {action_type} bearbeitet, dadurch Klimapunkte verloren und so dein wöchentliches Ziel nun nicht mehr erreicht. <span class="emoji">&#x1F622;</span>',
                                    request.user
                                    )
            if old_streak < new_streak:
                create_notification(request,
                                    f'Du hast eine neue Aktion vom Typen {action_type} bearbeitet und so deine Streak verkürzt. <span class="emoji">&#x1F973;</span>',
                                    request.user)
            elif old_streak > new_streak:
                create_notification(request,
                                    f'Du hast eine neue Aktion vom Typen {action_type} bearbeitet und so deine Streak verkürzt. <span class="emoji">&#x1F622;</span>',
                                    request.user)

            messages.success(request, all_messages["action_edited"])
            return redirect('history')

        if 'delete_action' in request.POST:
            old_level = get_level(request.user)
            old_weekly_goal_progress_percent = get_weekly_goal_from_user(request.user)[-1]
            old_streak = get_streak_from_user(request.user)
            action_type = current_action.aktion.name
            current_action.delete()
            new_level = get_level(request.user)
            new_weekly_goal_progress_percent = get_weekly_goal_from_user(request.user)[-1]
            new_streak = get_streak_from_user(request.user)
            if old_level['level_number'] > new_level['level_number']:
                create_notification(request,
                                    f'Du hast eine Aktion vom Typen {action_type} gelöscht, dadurch Klimapunkte verloren und bist so ins Level {new_level["current_level"].description} abgestiegen. <span class="emoji">&#x1F622;</span>',
                                    request.user)
            if new_weekly_goal_progress_percent < 100 <= old_weekly_goal_progress_percent:
                create_notification(request,
                                    f'Du hast eine neue Aktion vom Typen {action_type} gelöscht, dadurch Klimapunkte verloren und so dein wöchentliches Ziel nun nicht mehr erreicht. <span class="emoji">&#x1F622;</span>',
                                    request.user
                                    )
            if old_streak > new_streak:
                create_notification(request,
                                    f'Du hast eine neue Aktion vom Typen {action_type} gelöscht und so deine Streak verkürzt. <span class="emoji">&#x1F622;</span>',
                                    request.user)
                messages.success(request, all_messages["action_deleted"])
            return redirect('history')

    return render(request, './edit_action.html', {'categories': categories, 'current_action': current_action})


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
