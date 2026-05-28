from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from dotenv import load_dotenv

from aktionen.models import Aktion, AktionenListe
from community.models import Community
from core.all_messages import all_messages
from events.models import Event
from family.models import Family
from hall_of_fame.models import HallOfFameEntry
from home.models import Benachrichtigung
from personals.models import TreeCodes
from utils.functions import get_streak_from_user, get_additional_klimapunkte, get_klimapunkte, \
    get_weekly_goal_from_user, get_all_klimapunkte_from_user, get_level, get_families_of_user, create_notification, \
    get_perfect_week_progress, get_hall_of_fame_entries, get_family_rank_from_user

load_dotenv()


def home(request):
    klimapunkte_gesamt = 0
    user_count = 0
    for user in User.objects.prefetch_related():
        aktionen = Aktion.objects.filter(user=user)
        klimapunkte = get_klimapunkte(aktionen)
        klimapunkte += get_additional_klimapunkte(user)
        klimapunkte_gesamt += klimapunkte
        user_count += 1
    klimapunkte_gesamt = int(klimapunkte_gesamt)
    co2 = int(klimapunkte_gesamt / 1000)
    tree_count = TreeCodes.objects.filter(planted=True).count()
    return render(request, './home.html',
                  {'klimapunkte': klimapunkte_gesamt, 'user_count': user_count, 'co2': co2, 'tree_count': tree_count})


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('home')

    weekly_goal, weekly_klimapunkte, weekly_goal_progress_percent = get_weekly_goal_from_user(request.user)

    streak = get_streak_from_user(request.user)

    perfect_week_progress_de, perfect_week_progress_en = get_perfect_week_progress(request.user, date.today())

    perfect_week = False
    if weekly_goal_progress_percent >= 100:
        perfect_week = all(perfect_week_progress_de.values())

    aktionen = Aktion.objects.filter(user=request.user).order_by('-date')[:2]

    klimapunkte = get_all_klimapunkte_from_user(request.user)

    level = get_level(request.user)['current_level']

    hall_of_fame_entries = get_hall_of_fame_entries(request.user)

    worldwide_ranking_rank = get_family_rank_from_user(request.user, Family.objects.get(name='worldwide ranking'))

    return render(request, './dashboard.html',
                  {'weekly_goal': weekly_goal, 'weekly_goal_progress_percent': weekly_goal_progress_percent,
                   'weekly_klimapunkte': weekly_klimapunkte, 'streak': streak,
                   'perfect_week_progress_de': perfect_week_progress_de,
                   'perfect_week_progress_en': perfect_week_progress_en, 'perfect_week': perfect_week,
                   'aktionen': aktionen, 'klimapunkte': klimapunkte, 'level': level,
                   'hall_of_fame_entries': hall_of_fame_entries, 'worldwide_ranking_rank': worldwide_ranking_rank})


@login_required
def admin(request):
    if not request.user.is_staff:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect('dashboard')
    if request.method == 'POST':
        receiver = request.POST.get('receiver')
        name = request.POST.get('name')
        msg_de = request.POST.get('msg_de')
        msg_en = request.POST.get('msg_en')
        url = request.POST.get('url')

        if url is None or url == "":
            url = reverse('dashboard')

        if len(msg_de) > 500 or len(msg_en) > 500:
            messages.error(request, all_messages["too_long_input"])
            return redirect('admin')

        if not receiver or not name or not msg_de or not msg_en:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('admin')

        if receiver == 'user':
            try:
                user = User.objects.get(username=name)
            except User.DoesNotExist:
                messages.error(request, all_messages["admin__user_not_found"])
                return redirect('admin')
            create_notification(request, msg_de, msg_en, user, url)
            messages.success(request, all_messages["admin__successfully_sent_notification"])
        elif receiver == 'family-members':
            try:
                family = Family.objects.get(name=name)
            except Family.DoesNotExist:
                messages.error(request, all_messages["admin__family_not_found"])
                return redirect('admin')
            for user in family.members.all():
                create_notification(request, msg_de, msg_en, user, url)
            messages.success(request, all_messages["admin__successfully_sent_notification"])
        elif receiver == 'community-members':
            try:
                community = Community.objects.get(name=name)
            except Community.DoesNotExist:
                messages.error(request, all_messages["admin__community_not_found"])
                return redirect('admin')
            for family in community.members.all():
                for user in family.members.all():
                    create_notification(request, msg_de, msg_en, user, url)
            messages.success(request, all_messages["admin__successfully_sent_notification"])
        elif receiver == 'event-participants':
            try:
                event = Event.objects.get(id=name)
            except Event.DoesNotExist:
                messages.error(request, all_messages["admin__event_not_found"])
                return redirect('admin')
            for participant in event.participants.all():
                create_notification(request, msg_de, msg_en, participant, url)

            messages.success(request, all_messages["admin__successfully_sent_notification"])
        else:
            messages.error(request, all_messages["admin__invalid_receiver_type"])
            return redirect('admin')

    return render(request, 'admin.html')


@login_required
def count_benachrichtigungen(request):
    benachrichtigungen_count = Benachrichtigung.objects.filter(user=request.user).count()
    return JsonResponse({'benachrichtigungen_count': benachrichtigungen_count})


@login_required
def benachrichtigungen_view(request, benachrichtigungen_id = None):
    benachrichtigungen = Benachrichtigung.objects.filter(user=request.user).order_by('-date')
    return render(request, 'benachrichtigungen.html', {'benachrichtigungen': benachrichtigungen, 'id': benachrichtigungen_id})


@login_required
def delete_benachrichtigung(request, id):
    try:
        Benachrichtigung.objects.get(id=id).delete()
        messages.success(request, all_messages["notification_deleted"])
    except Benachrichtigung.DoesNotExist:
        messages.error(request, all_messages["delete_notification_error"])
    return redirect('benachrichtigungen_view')


def nutzungsbedingungen(request):
    return render(request, 'nutzungsbedingungen.html')


def actions_table(request):
    aktionen = AktionenListe.objects.all()
    return render(request, 'aktionenTable.html', {'aktionen': aktionen})


def datenschutz(request):
    return render(request, 'datenschutz.html')


def impressum(request):
    return render(request, 'impressum.html')


def companies_and_schools(request):
    return render(request, './companies_and_schools.html')


def support(request):
    return render(request, './support.html')


def feedback(request):
    return render(request, './feedback.html')
