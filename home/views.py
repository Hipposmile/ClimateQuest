import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import render, redirect
from dotenv import load_dotenv

from events.models import *
from forum.models import *
from verbrauch.models import *
from utils.functions import *

load_dotenv()

from core.all_messages import all_messages


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

    aktionen = Aktion.objects.filter(user=request.user).order_by('date')[:2]

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

    created_events = Event.objects.filter(creator=request.user, date_time__gte=timezone.now()).order_by('-date_time')[:2]
    events = request.user.events.filter(date_time__gte=timezone.now()).order_by('-date_time')[:2]

    created_artikel = Artikel.objects.filter(creator=request.user).order_by('-date_time')[:2]
    artikel = request.user.artikel_like.all().order_by('-date_time')[:2]

    created_forum_posts = ForumPost.objects.filter(creator=request.user).order_by('-date_time')[:2]
    forum_posts = ForumPost.objects.filter(answers__creator=request.user).distinct().order_by('-date_time')[:2]
    return render(request, './dashboard.html', {'aktionen': aktionen, 'klimapunkte': klimapunkte, 'level': level, 'families': families, 'communities_with_user_families': communities_with_user_families, 'created_events': created_events, 'events': events, 'created_artikel': created_artikel, 'artikel': artikel, 'created_forum_posts': created_forum_posts, 'forum_posts': forum_posts})

@login_required
def admin(request):
    if not request.user.is_staff:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect('dashboard')
    if request.method == 'POST':
        if 'benachrichtigung' in request.POST:
            receiver = request.POST.get('receiver')
            name = request.POST.get('name')
            msg = request.POST.get('msg')

            if len(msg) > 100:
                messages.error(request, all_messages["too_long_input"])
                return redirect('admin')

            if not receiver or not name or not msg:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('admin')
            
            if receiver == 'user':
                try:
                    user = User.objects.get(username=name)
                    create_notification(request, msg, user)
                    messages.success(request, all_messages["admin__successfully_sent_notification"])
                except User.DoesNotExist:
                    messages.error(request, all_messages["admin__user_not_found"])
                    return redirect('admin')
            elif receiver == 'family-members':
                try:
                    family = Family.objects.get(name=name)
                except Family.DoesNotExist:
                    messages.error(request, all_messages["admin__family_not_found"])
                    return redirect('admin')
                for user in family.members.all():
                    create_notification(request, msg, user)
                messages.success(request, all_messages["admin__successfully_sent_notification"])
            elif receiver == 'community-members':
                try:
                    community = Community.objects.get(name=name)
                except Community.DoesNotExist:
                    messages.error(request, all_messages["admin__community_not_found"])
                    return redirect('admin')
                for family in community.members.all():
                    for user in family.members.all():
                        create_notification(request, msg, user)
                messages.success(request, all_messages["admin__successfully_sent_notification"])
            elif receiver == 'event-participants':
                print("Sending to event participants")
                try:
                    event = Event.objects.get(id=name)
                except Event.DoesNotExist:
                    messages.error(request, all_messages["admin__event_not_found"])
                    return redirect('admin')
                print(event)
                for participant in event.participants.all():
                    create_notification(request, msg, participant)
                    print(participant.username)

                messages.success(request, all_messages["admin__successfully_sent_notification"])
            else:
                messages.error(request, all_messages["admin__invalid_receiver_type"])
                return redirect('admin')
        
        elif 'check_worldwide_ranking' in request.POST:
            try:
                worldwide_ranking = Family.objects.get(name='worldwide ranking', chat=False)
                if check_password(os.environ.get("WORLDWIDE_RANKING_PASSWORD", ""), worldwide_ranking.password) and check_password(os.environ.get("WORLDWIDE_RANKING_ADMIN_PASSWORD", ""), worldwide_ranking.admin_password):
                    messages.success(request, all_messages["worldwide_ranking_valid"])
                else:
                    worldwide_ranking_password = os.environ.get("WORLDWIDE_RANKING_PASSWORD", "")
                    worldwide_ranking.password = worldwide_ranking_password

                    worldwide_ranking_admin_password = os.environ.get("WORLDWIDE_RANKING_ADMIN_PASSWORD", "")
                    worldwide_ranking.admin_password = worldwide_ranking_admin_password

                    messages.error(request, all_messages["worldwide_ranking_invalid_passwords"])
            except Family.DoesNotExist:
                worldwide_ranking = Family.objects.create(
                    name='worldwide ranking',
                    password=os.environ.get("WORLDWIDE_RANKING_PASSWORD", ""),
                    admin_password=os.environ.get("WORLDWIDE_RANKING_PASSWORD", ""),
                    chat=False
                )
                for user in User.objects.all():
                    worldwide_ranking.members.add(user)
                    worldwide_ranking.save()
                messages.success(request, all_messages["worldwide_ranking_created"])
        elif 'add_everyone_user_erweitert' in request.POST:
            for user in User.objects.all():
                if not UserErweitert.objects.filter(user=user):
                    UserErweitert.objects.create(user=user)
            messages.success(request, all_messages["added_everyone_user_erweitert"])
        elif 'delete_user' in request.POST:
            username_to_delete = request.POST.get('username_to_delete')
            try:
                user = User.objects.get(username=username_to_delete)
                user.delete()
                messages.success(request, all_messages["user_deleted"])
            except User.DoesNotExist:
                messages.error(request, all_messages["user_not_found"])
        else:
            messages.error(request, all_messages["admin_invalid_action"])
            
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

def share(request):
    url = request.GET.get('url')
    if url is None:
        url = "https://climate-quest.de"
    return render(request, 'share.html', {'url': url})

def nutzungsbedingungen(request):
    return render(request, 'nutzungsbedingungen.html')

def actions_table(request):
    aktionen = AktionenListe.objects.all()
    return render(request, 'aktionenTable.html', {'aktionen': aktionen})

def datenschutz(request):
    return render(request, 'datenschutz.html')

def impressum(request):
    return render(request, 'impressum.html')
