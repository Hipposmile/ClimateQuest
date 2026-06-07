from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import gettext as _

from aktionen.models import Aktion, AktionenListe, Category
from aktionen.views import validate_number, get_period_start, action_date_invalid, get_if_timely_action
from core.all_messages import all_messages
from family.models import Family
from personals.models import UserErweitert
from utils.functions import dezimalstellen, get_additional_klimapunkte, get_weekly_goal_from_user, \
    get_streak_from_user, send_mail_function, get_level, create_notification, get_all_klimapunkte_from_user, \
    get_family_rank_from_user, get_date_range, get_klimapunkte_for_member, get_hall_of_fame_entries
from home.models import ReportedUser


def get_user(request, user_id, allow_needed=True):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, all_messages["user_not_found"])
        return False
    if allow_needed and user != request.user and not user.usererweitert.allows_data_view:
        messages.error(request, all_messages["user_blocked_view"])
        return False
    return user


"""def klimapunkte_view(request, user_id):
    user = get_user(request, user_id)
    if not user:
        return redirect('user_detail', user_id)

    zeitraum = 'gesamt'
    aktionen = Aktion.objects.filter(user=user)
    klimapunkte = get_klimapunkte(aktionen)

    if request.method == 'POST':
        heute = date.today()
        seven_days = date.today() - timedelta(days=7)
        thirty_days = date.today() - timedelta(days=30)
        threehundertsixtyfive_days = date.today() - timedelta(days=365)

        zeitraum = request.POST.get('zeitraum')

        if zeitraum == 'heute':
            aktionen = Aktion.objects.filter(user=user, date=heute)
            klimapunkte = get_klimapunkte(aktionen)

        elif zeitraum == 'sieben Tage':
            aktionen = Aktion.objects.filter(user=user, date__gte=seven_days)
            klimapunkte = get_klimapunkte(aktionen)

        elif zeitraum == 'dreißig Tage':
            aktionen = Aktion.objects.filter(user=user, date__gte=thirty_days)
            klimapunkte = get_klimapunkte(aktionen)

        elif zeitraum == 'dreihundertfünfundsechzig Tage':
            aktionen = Aktion.objects.filter(user=user, date__gte=threehundertsixtyfive_days)
            klimapunkte = get_klimapunkte(aktionen)

        elif zeitraum == 'gesamt':
            aktionen = Aktion.objects.filter(user=user)
            klimapunkte = get_klimapunkte(aktionen)

        elif zeitraum == 'benutzerdefiniert':
            start_datum = request.POST.get('start_date')
            end_datum = request.POST.get('end_date')
            if not start_datum or not end_datum:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('klimapunkte_view', user_id)
            try:
                start_datum = datetime.strptime(start_datum, '%Y-%m-%d').date()
                end_datum = datetime.strptime(end_datum, '%Y-%m-%d').date()
                if start_datum > end_datum:
                    messages.error(request, all_messages["invalid_date_range"])
                    return redirect('klimapunkte_view', user_id)
                if end_datum > heute:
                    messages.error(request, all_messages["date_in_future"])
                    return redirect('klimapunkte_view', user_id)
            except ValueError:
                messages.error(request, all_messages["invalid_date"])
                return redirect('klimapunkte_view', user_id)
            aktionen = Aktion.objects.filter(user=user, date__range=(start_datum, end_datum))
            klimapunkte = get_klimapunkte(aktionen)
            zeitraum = f'von {start_datum} bis {end_datum}'
        else:
            messages.error(request, all_messages["invalid_time_period"])
            return redirect('klimapunkte_view', user_id)

        if klimapunkte is None:
            klimapunkte = 0

    aktionen_klimapunkte = get_klimapunkte_from_likes(user)

    klimapunkte_total = klimapunkte + aktionen_klimapunkte

    return render(request, './klimapunkte.html',
                  {'klimapunkte': klimapunkte, 'aktionen_klimapunkte': aktionen_klimapunkte,
                   'klimapunkte_total': klimapunkte_total, 'zeitraum': zeitraum, 'user': user})"""

VALID_ZEITRAEUME_KLIMAPUNKTE = {'Heute', 'Sieben Tage', 'Dreißig Tage', 'Dreihundertfünfundsechzig Tage', 'Gesamt',
                                'Benutzerdefiniert'}


@login_required
def klimapunkte_view(request, user_id):
    user = get_user(request, user_id)
    if not user:
        return redirect('user_detail', user_id)

    heute = date.today()
    zeitraum_text = _("Gesamt")
    start_datum = end_datum = None

    if request.method == 'POST':
        zeitraum = request.POST.get('zeitraum', 'Gesamt')

        if zeitraum not in VALID_ZEITRAEUME_KLIMAPUNKTE:
            messages.error(request, all_messages["invalid_time_period"])
            return redirect('klimapunkte_view', user_id)

        if zeitraum == 'Benutzerdefiniert':
            raw_start = request.POST.get('start_date')
            raw_end = request.POST.get('end_date')

            if not raw_start or not raw_end:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('klimapunkte_view', user_id)

            try:
                start_datum = datetime.strptime(raw_start, '%Y-%m-%d').date()
                end_datum = datetime.strptime(raw_end, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, all_messages["invalid_date"])
                return redirect('klimapunkte_view', user_id)

            if start_datum > end_datum:
                messages.error(request, all_messages["invalid_date_range"])
                return redirect('klimapunkte_view', user_id)
            if end_datum > heute:
                messages.error(request, all_messages["date_in_future"])
                return redirect('klimapunkte_view', user_id)

            zeitraum_text = _("%(start)s bis %(end)s") % {
                'start': start_datum.strftime('%d.%m.%Y') if request.LANGUAGE_CODE == 'de' else start_datum.strftime(
                    '%m/%d/%Y'),
                'end': end_datum.strftime('%d.%m.%Y') if request.LANGUAGE_CODE == 'de' else end_datum.strftime(
                    '%m/%d/%Y'),
            }
        else:
            start_datum, end_datum = get_date_range(zeitraum, heute)

            if zeitraum == 'heute':
                start_datum = end_datum = heute

            if request.LANGUAGE_CODE == 'en':
                zeitraum_text_translations = {
                    'Gesamt': 'Total',
                    'Heute': 'Today',
                    'Sieben Tage': 'Seven days',
                    'Dreißig Tage': 'Thirty days',
                    'Dreihundertfünfundsechzig Tage': 'Threehundredsixtyfive days',
                }
                zeitraum_text = zeitraum_text_translations.get(zeitraum)
            else:
                zeitraum_text = zeitraum

    additional_klimapunkte = get_additional_klimapunkte(user)
    klimapunkte = get_klimapunkte_for_member(user, start_datum, end_datum)
    klimapunkte_total = klimapunkte + additional_klimapunkte

    saved_co2 = klimapunkte / 1000

    return render(request, './klimapunkte.html', {
        'klimapunkte': klimapunkte,
        'additional_klimapunkte': additional_klimapunkte,
        'klimapunkte_total': klimapunkte_total,
        'saved_co2': saved_co2,
        'zeitraum': zeitraum_text,
        'user': user,
    })


def level_view(request, user_id):
    user = get_user(request, user_id)
    if not user:
        return redirect('user_detail', user_id)

    level_data = get_level(user)
    return render(request, './level.html', {'level_data': level_data, 'user': user})


def history(request, user_id):
    user = get_user(request, user_id)
    if not user:
        return redirect('user_detail', user_id)

    actions = Aktion.objects.filter(user=user).order_by('-date')
    return render(request, './history.html', {'actions': actions, 'user': user})


def users_overview(request):
    if request.method == 'POST':
        search_keyword = request.POST.get('search_keyword')
        users = User.objects.filter(username__icontains=search_keyword)
        return render(request, 'users_overview.html', {'users': users, 'search_keyword': search_keyword})
    return render(request, 'users_overview.html')


def user_detail(request, user_id):
    user = get_user(request, user_id, False)
    if not user:
        return redirect('dashboard')

    user_expanded = UserErweitert.objects.get(user=user)
    weekly_goal, weekly_klimapunkte, weekly_goal_progress_percent = get_weekly_goal_from_user(user)
    streak = get_streak_from_user(user)
    all_klimapunkte = get_all_klimapunkte_from_user(user)
    worldwide_ranking_rank = get_family_rank_from_user(user, Family.objects.get(name='worldwide ranking'))
    hall_of_fame_entries = get_hall_of_fame_entries(user)

    if request.user.is_authenticated:
        if request.method == 'POST':
            reason = request.POST.get('reason')
            report_user(request, user, request.user, reason)
            messages.success(request, all_messages["reported_user"])

    return render(request, './user_detail.html', {'user_expanded': user_expanded, 'weekly_goal': weekly_goal,
                                                  'weekly_goal_progress_percent': weekly_goal_progress_percent,
                                                  'weekly_klimapunkte': weekly_klimapunkte, 'streak': streak,
                                                  'all_klimapunkte': all_klimapunkte,
                                                  'worldwide_ranking_rank': worldwide_ranking_rank,
                                                  'hall_of_fame_entries': hall_of_fame_entries})


def action_detail(request, action_id, user_id):
    user = get_user(request, user_id)
    if not user:
        return redirect('user_detail', user_id)

    try:
        current_action = Aktion.objects.get(id=action_id, user=user)
    except Aktion.DoesNotExist:
        messages.error(request, all_messages["action_not_found"])
        return redirect('history_me')

    categories = Category.objects.all().order_by('name')

    if request.user == user:
        if request.method == 'POST':
            if 'edit_action' in request.POST:
                is_truth = request.POST.get('is_truth') == 'on'
                if not is_truth:
                    messages.error(request, all_messages["not_is_truth"])
                    return redirect('action_detail', action_id, user_id)

                action_type_id = request.POST.get('action_type_id')
                if not action_type_id:
                    messages.error(request, all_messages["action_name_missing"])
                    return redirect('action_detail', action_id, user_id)
                try:
                    action = AktionenListe.objects.get(id=action_type_id)
                except AktionenListe.DoesNotExist:
                    messages.error(request, all_messages["action_not_found"])
                    return redirect('action_detail', action_id, user_id)

                action_description = request.POST.get('action_description')
                if len(action_description) > 200:
                    messages.error(request, all_messages["too_long_input"])
                    return redirect('action_detail', action_id, user_id)

                action_quantity = request.POST.get('action_quantity')
                if not action_quantity:
                    messages.error(request, all_messages["missing_required_inputs"])
                    return redirect('action_detail', action_id, user_id)
                try:
                    action_quantity = validate_number(action_quantity, dezimalstellen)
                except ValueError:
                    messages.error(request, all_messages["action_invalid_quantity"])
                    return redirect('action_detail', action_id, user_id)
                if action_quantity <= 0 or action_quantity is False:
                    messages.error(request, all_messages["invalid_quantity"])
                    return redirect('action_detail', action_id, user_id)
                elif not get_if_timely_action(action.mengeBeschreibungSingular) and (
                        Aktion.objects.filter(user=request.user, aktion=action, date=date.today()).aggregate(
                            total=Sum('quantity'))["total"] or 0) + action_quantity > action.max:
                    messages.error(request, all_messages["max_action_quantity"])
                    return redirect('action_detail', action_id, user_id)

                action_date = current_action.date

                action_start = get_period_start(action_date, action_quantity, action.mengeBeschreibungSingular.lower())

                if action_date > datetime.now().date():
                    messages.error(request, all_messages["date_in_future"])
                    return redirect('action_detail', action_id, user_id)
                if action_start:
                    if action_start < date.today() - relativedelta(months=1):
                        messages.error(request, all_messages["action_too_past"])
                        return redirect('action_detail', action_id, user_id)
                else:
                    if action_date < date.today() - relativedelta(months=1):
                        messages.error(request, all_messages["action_too_past"])
                        return redirect('add')

                if action_date_invalid(action, action_date, action_quantity, request.user, action_id):
                    messages.error(request, all_messages["action_already_set_in_period"])
                    return redirect('action_detail', action_id, user_id)

                old_level = get_level(request.user)
                old_streak = get_streak_from_user(request.user)

                current_action.aktion = action
                current_action.description = action_description
                current_action.user = request.user
                current_action.quantity = action_quantity
                current_action.save()

                new_level = get_level(request.user)
                new_streak = get_streak_from_user(request.user)

                if old_level['level_number'] < new_level['level_number']:
                    create_notification(request,
                                        f'Du hast eine Aktion vom Typen {action.name} bearbeitet und bist so ins Level {new_level["current_level"].description} aufgestiegen. <span class="emoji">&#x1F973;</span>',
                                        f'You edited an action (type: {action.name_en}) and so reached level {new_level["current_level"].description}. <span class="emoji">&#x1F973;</span>',
                                        request.user,
                                        url=reverse('level_me'))
                    if request.LANGUAGE_CODE == "de":
                        messages.success(request,
                                         f'Du hast eine Aktion vom Typen {action.name} bearbeitet und bist so ins Level {new_level["current_level"].description} aufgestiegen. <span class="emoji">&#x1F973;</span>')
                    else:
                        messages.success(request,
                                         f'You edited an action (type: {action.name_en}) and so reached level {new_level["current_level"].description}. <span class="emoji">&#x1F973;</span>')

                elif old_level['level_number'] > new_level['level_number']:
                    create_notification(request,
                                        f'Du hast eine Aktion vom Typen {action.name} bearbeitet, dadurch Klimapunkte verloren und bist so ins Level {new_level["current_level"].description} abgestiegen. <span class="emoji">&#x1F622;</span>',
                                        f'You edited an action (type: {action.name_en}), lost climate points and so descended to level {new_level["current_level"].description_en}. <span class="emoji">&#x1F622;</span>',
                                        request.user,
                                        url=reverse('level_me'))

                    if request.LANGUAGE_CODE == 'de':
                        messages.success(request,
                                         f'Du hast eine Aktion vom Typen {action.name} bearbeitet, dadurch Klimapunkte verloren und bist so ins Level {new_level["current_level"].description} abgestiegen. <span class="emoji">&#x1F622;</span>')
                    else:
                        messages.success(request,
                                         f'You edited an action (type: {action.name_en}), lost climate points and so descended to level {new_level["current_level"].description_en}. <span class="emoji">&#x1F622;</span>')

                if old_streak < new_streak:
                    create_notification(request,
                                        f'Du hast eine Aktion vom Typen {action.name} bearbeitet und so deine Streak verlängert. <span class="emoji">&#x1F973;</span>',
                                        f'You edited an action (type: {action.name_en}) and so extended your streak. <span class="emoji">&#x1F973;</span>',
                                        request.user,
                                        url=reverse('dashboard'))

                    if request.LANGUAGE_CODE == 'de':
                        messages.success(request,
                                         f'Du hast eine Aktion vom Typen {action.name} bearbeitet und so deine Streak verlängert. <span class="emoji">&#x1F973;</span>')
                    else:
                        messages.success(request,
                                         f'You edited an action (type: {action.name_en}) and so extended your streak. <span class="emoji">&#x1F973;</span>')

                elif old_streak > new_streak:
                    create_notification(request,
                                        f'Du hast eine Aktion vom Typen {action.name} bearbeitet und so deine Streak verkürzt. <span class="emoji">&#x1F622;</span>',
                                        f'You edited an action (type: {action.name_en}) and so shortened your streak. <span class="emoji">&#x1F622;</span>',
                                        request.user,
                                        url=reverse('dashboard'))

                    if request.LANGUAGE_CODE == "de":
                        messages.error(request,
                                       f'Du hast eine Aktion vom Typen {action.name} bearbeitet und so deine Streak verkürzt. <span class="emoji">&#x1F622;</span>')
                    else:
                        messages.success(request,
                                         f'You edited an action (type: {action.name_en}) and so shortened your streak. <span class="emoji">&#x1F622;</span>')

                messages.success(request, all_messages["action_edited"])
                return redirect('action_detail', action_id, user_id)

            if 'delete_action' in request.POST:
                old_level = get_level(request.user)
                old_streak = get_streak_from_user(request.user)
                action_type = current_action.aktion
                current_action.delete()
                new_level = get_level(request.user)
                new_streak = get_streak_from_user(request.user)
                if old_level['level_number'] > new_level['level_number']:
                    create_notification(request,
                                        f'Du hast eine Aktion vom Typen {action_type.name} gelöscht, dadurch Klimapunkte verloren und bist so ins Level {new_level["current_level"].description} abgestiegen. <span class="emoji">&#x1F622;</span>',
                                        f'You deleted an action (type: {action_type.name_en}), lost climate points and so descended to level {new_level["current_level"].description}. <span class="emoji">&#x1F622;</span>',
                                        request.user,
                                        url=reverse('level_me'))
                    if request.LANGUAGE_CODE == "de":
                        messages.error(request,
                                       f'Du hast eine Aktion vom Typen {action_type} gelöscht, dadurch Klimapunkte verloren und bist so ins Level {new_level["current_level"].description} abgestiegen. <span class="emoji">&#x1F622;</span>')
                    else:
                        messages.error(request,
                                       f'You deleted an action (type: {action_type.name_en}), lost climate points and so descended to level {new_level["current_level"].description}. <span class="emoji">&#x1F622;</span>')
                if old_streak > new_streak:
                    create_notification(request,
                                        f'Du hast eine Aktion vom Typen {action_type.name} gelöscht und so deine Streak verkürzt. <span class="emoji">&#x1F622;</span>',
                                        f'You deleted an action (type: {action_type.name_en}) and so shortened your streak. <span class="emoji">&#x1F622;</span>',
                                        request.user,
                                        url=reverse('dashboard'))
                    if request.LANGUAGE_CODE == "de":
                        messages.error(request,
                                       f'Du hast eine Aktion vom Typen {action_type} gelöscht und so deine Streak verkürzt. <span class="emoji">&#x1F622;</span>')
                    else:
                        messages.error(request,
                                       f'You deleted an action (type: {action_type.name_en}) and so shortened your streak. <span class="emoji">&#x1F622;</span>')
                messages.success(request, all_messages["action_deleted"])
                return redirect('history_me')

    return render(request, './action_detail.html',
                  {'categories': categories, 'current_action': current_action, 'user': user})


@login_required
def klimapunkte_me(request):
    return redirect('klimapunkte_view', request.user.id)


@login_required
def level_me(request):
    return redirect('level_view', request.user.id)


@login_required()
def history_me(request):
    return redirect('history', request.user.id)


@login_required
def report_user(request, reported_user, reporting_user, reason):
    reported_user_model = ReportedUser.objects.create(reported_user=reported_user, reporting_user=reporting_user,
                                                      reason=reason)

    admin = User.objects.get(is_superuser=True, is_staff=True, username='admin')
    send_mail_function(
        request=request,
        subject=f"User {reported_user.username} wurde von {reporting_user.username} gemeldet",
        message=f"""
            <h2>Gemeldeter User</h2>
            <p>Username: {reported_user.username}</p>
            <p>ID: {reported_user.id}</p>
            <h2>Meldender User</h2>
            <p>Username: {reporting_user.username}</p>
            <p>ID: {reporting_user.id}</p>
            <h2>Begründung</h2>
            <p>{reason}</p>
        """,
        user=admin,
        url=f'/ClimateQuestAdmin/home/reporteduser/{reported_user_model.id}/change/',
    )
