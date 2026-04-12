from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from dotenv import load_dotenv

from aktionen.models import Aktion, AktionenListe
from artikel.models import Artikel
from community.models import Community
from core.all_messages import all_messages
from events.models import Event
from family.models import Family
from forum.models import ForumPost
from home.models import Benachrichtigung
from utils.functions import get_streak_from_user, get_klimapunkte_from_likes, get_klimapunkte, \
    get_weekly_goal_from_user, get_all_klimapunkte_from_user, get_level, get_families_of_user, create_notification, \
    get_perfect_week_progress

load_dotenv()


def home(request):
    klimapunkte_gesamt = 0
    user_count = 0
    for user in User.objects.prefetch_related():
        aktionen = Aktion.objects.filter(user=user)
        klimapunkte = get_klimapunkte(aktionen)
        klimapunkte += get_klimapunkte_from_likes(user)
        klimapunkte_gesamt += klimapunkte
        user_count += 1
    return render(request, './home.html', {'klimapunkte': klimapunkte_gesamt, 'user_count': user_count})


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('home')

    weekly_goal, weekly_klimapunkte, weekly_goal_progress_percent = get_weekly_goal_from_user(request.user)

    streak = get_streak_from_user(request.user)

    perfect_week_progress = get_perfect_week_progress(request.user, date.today())

    perfect_week = False
    if weekly_goal_progress_percent >= 100:
        perfect_week = all(perfect_week_progress.values())

    aktionen = Aktion.objects.filter(user=request.user).order_by('-date')[:2]

    klimapunkte = get_all_klimapunkte_from_user(request.user)

    level = get_level(request.user)['current_level']

    families = get_families_of_user(request.user).order_by('name')[:2]

    communities = Community.objects.filter(members__id__in=families).distinct().order_by('name')[:2]

    communities_with_user_families = []

    for community in communities:
        families_in_community = community.members.all()  # alle Families in dieser Community
        families_user_belongs_to = families_in_community & families  # Schnittmenge
        communities_with_user_families.append({'community': community, 'families': families_user_belongs_to})

    families = families[:2]

    created_events = Event.objects.filter(creator=request.user, date_time__gte=timezone.now()).order_by('-date_time')[
        :2]
    events = request.user.events.filter(date_time__gte=timezone.now()).order_by('-date_time')[:2]

    created_artikel = Artikel.objects.filter(creator=request.user).order_by('-date_time')[:2]
    artikel = request.user.artikel_like.all().order_by('-date_time')[:2]

    created_forum_posts = ForumPost.objects.filter(creator=request.user).order_by('-date_time')[:2]
    forum_posts = ForumPost.objects.filter(answers__creator=request.user).distinct().order_by('-date_time')[:2]
    return render(request, './dashboard.html',
                  {'weekly_goal': weekly_goal, 'weekly_goal_progress_percent': weekly_goal_progress_percent,
                   'weekly_klimapunkte': weekly_klimapunkte, 'streak': streak,
                   'perfect_week_progress': perfect_week_progress, "perfect_week": perfect_week,
                   'aktionen': aktionen, 'klimapunkte': klimapunkte, 'level': level, 'families': families,
                   'communities_with_user_families': communities_with_user_families, 'created_events': created_events,
                   'events': events, 'created_artikel': created_artikel, 'artikel': artikel,
                   'created_forum_posts': created_forum_posts, 'forum_posts': forum_posts})


@login_required
def admin(request):
    if not request.user.is_staff:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect('dashboard')
    if request.method == 'POST':
        receiver = request.POST.get('receiver')
        name = request.POST.get('name')
        msg = request.POST.get('msg')
        url = request.POST.get('url')

        if url is None or url == "":
            url = reverse('dashboard')

        if len(msg) > 500:
            messages.error(request, all_messages["too_long_input"])
            return redirect('admin')

        if not receiver or not name or not msg:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('admin')

        if receiver == 'user':
            try:
                user = User.objects.get(username=name)
            except User.DoesNotExist:
                messages.error(request, all_messages["admin__user_not_found"])
                return redirect('admin')
            create_notification(request, msg, user, url)
            messages.success(request, all_messages["admin__successfully_sent_notification"])
        elif receiver == 'family-members':
            try:
                family = Family.objects.get(name=name)
            except Family.DoesNotExist:
                messages.error(request, all_messages["admin__family_not_found"])
                return redirect('admin')
            for user in family.members.all():
                create_notification(request, msg, user, url)
            messages.success(request, all_messages["admin__successfully_sent_notification"])
        elif receiver == 'community-members':
            try:
                community = Community.objects.get(name=name)
            except Community.DoesNotExist:
                messages.error(request, all_messages["admin__community_not_found"])
                return redirect('admin')
            for family in community.members.all():
                for user in family.members.all():
                    create_notification(request, msg, user, url)
            messages.success(request, all_messages["admin__successfully_sent_notification"])
        elif receiver == 'event-participants':
            try:
                event = Event.objects.get(id=name)
            except Event.DoesNotExist:
                messages.error(request, all_messages["admin__event_not_found"])
                return redirect('admin')
            for participant in event.participants.all():
                create_notification(request, msg, participant, url)

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
def benachrichtigungen_view(request):
    benachrichtigungen = Benachrichtigung.objects.filter(user=request.user).order_by('-date')
    return render(request, 'benachrichtigungen.html', {'benachrichtigungen': benachrichtigungen})


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
