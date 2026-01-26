from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from core.all_messages import all_messages
from utils.functions import *


@login_required
def klimapunkte_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, all_messages["user_not_found"])
        return redirect('dashboard')

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
                   'klimapunkte_total': klimapunkte_total, 'zeitraum': zeitraum, 'user': user})


@login_required
def level_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, all_messages["user_not_found"])
        return redirect('dashboard')

    level_data = get_level(user)
    return render(request, './level.html', {'level_data': level_data, 'user': user})


@login_required
def history(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, all_messages["user_not_found"])
        return redirect('dashboard')

    actions = Aktion.objects.filter(user=user).order_by('-date')
    return render(request, './history.html', {'actions': actions})


@login_required
def users_overview(request):
    if request.method == 'POST':
        search_keyword = request.POST.get('search_keyword')
        users = User.objects.filter(username__icontains=search_keyword)
        return render(request, 'users_overview.html', {'users': users})
    return render(request, 'users_overview.html')


@login_required
def user_detail(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, all_messages["user_not_found"])
        return redirect('users_overview')

    user_expanded = UserErweitert.objects.get(user=user)
    weekly_goal, weekly_klimapunkte, weekly_goal_progress_percent = get_weekly_goal_from_user(user)
    streak = get_streak_from_user(user)

    if request.method == 'POST':
        reason = request.POST.get('reason')
        report_user(request, user, request.user, reason)
        messages.success(request, all_messages["reported_user"])

    return render(request, './user_detail.html', {'user_expanded': user_expanded, 'weekly_goal': weekly_goal,
                                                  'weekly_goal_progress_percent': weekly_goal_progress_percent,
                                                  'weekly_klimapunkte': weekly_klimapunkte, 'streak': streak})


@login_required
def klimapunkte_me(request):
    return redirect('klimapunkte_view', request.user.id)


@login_required
def level_me(request):
    return redirect('level_view', request.user.id)


def history_me(request):
    return redirect('history', request.user.id)


def report_user(request, reported_user, reporting_user, reason):
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
    )
