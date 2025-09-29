from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q
from datetime import date, timedelta, datetime

from core.all_messages import all_messages
from .models import *
from utils.functions import *
from verbrauch.models import *

from datetime import datetime, timedelta, date
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.db.models import Q


"""def get_community_or_redirect(request, community_id):
    if not community_id:
        messages.error(request, all_messages["community_id_missing"])
        return None
    try:
        return Community.objects.prefetch_related('members__members').get(id=community_id)
    except Community.DoesNotExist:
        messages.error(request, all_messages["community_not_found"])
        return None

def get_family_or_redirect(request, family_id):
    if not family_id:
        messages.error(request, all_messages["community__family_id_missing"])
        return None
    try:
        return Family.objects.prefetch_related('members').get(id=family_id)
    except Family.DoesNotExist:
        messages.error(request, all_messages["community__family_not_found"])
        return None

def is_valid_admin(request, password, actual_password, error_key):
    if not password:
        messages.error(request, all_messages["missing_required_inputs"])
        return False
    if not check_password(password, actual_password):
        messages.error(request, all_messages["invalid_admin_password"])
        return False
    return True

def notify_community_users(request, community, message, exclude_user=None):
    for user in community.user_members():
        if exclude_user and user == exclude_user:
            continue
        createBenachrichtigung(request, message, user)

def handle_change_communityname(request, community):
    admin_password = request.POST.get('admin_password')
    new_name = request.POST.get('new_communityname')
    if not is_valid_admin(request, admin_password, community.admin_password, "admin_password_or_name_missing"):
        return
    old_name = community.name
    community.name = new_name
    community.save()
    messages.success(request, all_messages["community_name_changed"])
    notify_community_users(request, community, f'Der Communityname wurde von {old_name} zu {new_name} geändert')

def handle_change_password(request, community):
    admin_password = request.POST.get('admin_password')
    new_password = request.POST.get('new_password')
    if not is_valid_admin(request, admin_password, community.admin_password, "password_missing"):
        return
    community.password = new_password
    community.save()
    notify_community_users(request, community, f'Das Passwort der Community {community.name} wurde geändert')
    messages.success(request, all_messages["community_password_changed"])

def handle_change_admin_password(request, community):
    current_password = request.POST.get('current_admin_password')
    new_password = request.POST.get('new_admin_password')
    if not is_valid_admin(request, current_password, community.admin_password, "current_admin_password_missing"):
        return
    community.admin_password = new_password
    community.save()
    notify_community_users(request, community, f'Das Admin-Passwort der Community {community.name} wurde geändert')
    messages.success(request, all_messages["admin_password_changed"])

def handle_remove_member(request, community, family):
    admin_password = request.POST.get('admin_password')
    family_name = request.POST.get('family_name')
    if not is_valid_admin(request, admin_password, community.admin_password, "remove_admin_password_or_family_missing"):
        return
    try:
        family_to_remove = Family.objects.get(name=family_name)
        community.members.remove(family_to_remove)
        notify_community_users(request, community, f'Die Family {family_to_remove.name} wurde von {request.user} aus der Community {community.name} entfernt')
        messages.success(request, all_messages["community__family_removed"])
    except Family.DoesNotExist:
        messages.error(request, all_messages["community__family_not_found"])

def handle_leave_community(request, community, family):
    password = request.POST.get('family_admin_password')
    if not is_valid_admin(request, password, family.admin_password, "delete_admin_password_missing"):
        return
    community.members.remove(family)
    notify_community_users(request, community, f'Die Family {family.name} wurde von {request.user} aus der Community {community.name} entfernt')
    messages.success(request, all_messages["family_left_community"])

def handle_delete_community(request, community):
    admin_password = request.POST.get('admin_password')
    if not is_valid_admin(request, admin_password, community.admin_password, "delete_admin_password_missing"):
        return
    notify_community_users(request, community, f'Die Community {community.name} wurde von {request.user} gelöscht')
    community.delete()
    messages.success(request, all_messages["community_deleted"])

def get_family_by_name_and_password(request, name, password, redirect_view):
    try:
        family = Family.objects.prefetch_related('members').get(name=name)
        if not check_password(password, family.admin_password):
            raise ValueError
        return family
    except (Family.DoesNotExist, ValueError):
        messages.error(request, all_messages["community__invalid_family_credentials"])
        return redirect(redirect_view)

def get_community_by_name_and_password(request, name, password, redirect_view):
    try:
        community = Community.objects.prefetch_related('members__members').get(name=name)
        if not check_password(password, community.password):
            raise ValueError
        return community
    except (Community.DoesNotExist, ValueError):
        messages.error(request, all_messages["invalid_community_credentials"])
        return redirect(redirect_view)

def notify_family_members(request, family, message):
    for user in family.members.all():
        createBenachrichtigung(request, message, user)

@login_required
def create_community(request):
    if request.method == 'POST':
        data = request.POST
        required_fields = ['communityname', 'community_password', 'community_admin_password', 'familyname', 'family_admin_password']
        if not all(data.get(field) for field in required_fields):
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('create_community')

        if Community.objects.filter(name=data['communityname']).exists():
            messages.error(request, all_messages["community_exists"])
            return redirect('create_community')

        family = get_family_by_name_and_password(request, data['familyname'], data['family_admin_password'], 'create_community')
        if isinstance(family, HttpResponseRedirect):
            return family

        community = Community.objects.create(
            name=data['communityname'],
            password=data['community_password'],
            admin_password=data['community_admin_password']
        )
        community.members.add(family)

        createBenachrichtigung(request, f'Du hast die Community {community.name} mit der Family {family.name} erstellt', request.user)
        notify_family_members(request, family, f'Die Family {family.name} ist der Community {community.name} beigetreten')
        messages.success(request, all_messages["community_created"])
        return redirect('communities_view')

    return render(request, 'create_community.html')

@login_required
def join_community(request):
    if request.method == 'POST':
        data = request.POST
        required_fields = ['communityname', 'community_password', 'familyname', 'family_admin_password']
        if not all(data.get(field) for field in required_fields):
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('join_community')

        family = get_family_by_name_and_password(request, data['familyname'], data['family_admin_password'], 'join_community')
        if isinstance(family, HttpResponseRedirect):
            return family

        try:
            community = Community.objects.prefetch_related('members__members').get(name=data['communityname'])
        except Community.DoesNotExist:
            messages.error(request, all_messages["invalid_community_credentials"])
            return redirect('join_community')

        if family in community.members.all():
            messages.error(request, all_messages["community__family_already_joined"])
            return redirect('join_community')

        if not check_password(data['community_password'], community.password):
            messages.error(request, all_messages["invalid_community_credentials"])
            return redirect('join_community')

        community.members.add(family)
        notify_family_members(request, family, f'Die Family {family.name} ist der Community {community.name} beigetreten')
        messages.success(request, all_messages["community_joined"].format(family=family, community=community))
        return redirect('communities_view')

    return render(request, 'join_community.html')

@login_required
def communities_view(request):
    user_families = getFamiliesOfUser(request.user)
    communities = Community.objects.filter(members__in=user_families).distinct().prefetch_related('members').order_by('name')

    communities_with_user_families = [
        {
            'community': community,
            'families': [fam for fam in community.members.all() if fam in user_families]
        }
        for community in communities
    ]

    return render(request, 'communities.html', {'communities_with_user_families': communities_with_user_families})


@login_required
def community_detail(request, community_id, family_id):
    if not community_id:
        messages.error(request, all_messages["community_id_missing"])
        return redirect('communities_view')

    if not family_id:
        messages.error(request, all_messages["community__family_id_missing"])
        return redirect('communities_view')

    try:
        community = Community.objects.prefetch_related('members__members').get(id=community_id)
    except Community.DoesNotExist:
        messages.error(request, all_messages["community_not_found"])
        return redirect('home')

    try:
        family = Family.objects.prefetch_related('members').get(id=family_id)
    except Family.DoesNotExist:
        messages.error(request, all_messages["community__family_not_found"])
        return redirect('home')

    if request.user not in family.members.all():
        messages.error(request, all_messages["community__not_member_of_family"])
        return redirect('home')

    zeitraum = request.POST.get('zeitraum', 'gesamt')
    heute = date.today()

    # Zeitfilter bestimmen
    date_filter = Q()
    zeitraum_text = zeitraum
    if zeitraum == 'heute':
        date_filter = Q(date=heute)
    elif zeitraum == 'sieben Tage':
        date_filter = Q(date__gte=heute - timedelta(days=7))
    elif zeitraum == 'dreißig Tage':
        date_filter = Q(date__gte=heute - timedelta(days=30))
    elif zeitraum == 'dreihundertfünfundsechzig Tage':
        date_filter = Q(date__gte=heute - timedelta(days=365))
    elif zeitraum == 'benutzerdefiniert':
        try:
            start = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
            end = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d').date()
            if start > end or end > heute:
                raise ValueError
            date_filter = Q(date__range=(start, end))
            zeitraum_text = f'von {start} bis {end}'
        except (TypeError, ValueError):
            messages.error(request, all_messages["invalid_date_range"])
            return redirect('community_detail')

    # Alle Mitglieder aller Familien in der Community
    all_family_members = []
    for fam in community.members.all():
        all_family_members.extend(fam.members.all())

    # Aktionen aller Mitglieder auf einmal laden
    aktionen = Aktion.objects.filter(user__in=all_family_members).filter(date_filter).select_related('user')

    # Aktionen pro Community-Mitglied aggregieren
    members_with_klimapunkte = []
    for fam in community.members.all():
        members = list(fam.members.all())
        member_ids = [m.id for m in members]
        aktionen_fam = [a for a in aktionen if a.user_id in member_ids]
        klimapunkte_gesamt = get_klimapunkte(aktionen_fam)
        klimapunkte = klimapunkte_gesamt / len(members) if members else 0
        members_with_klimapunkte.append({
            'member': fam,
            'klimapunkte': klimapunkte,
            'family_members': members
        })

    if filter == "Klimapunkte":
        sort_key = 'klimapunkte'
        reverse_sort = True
    elif filter == "Username":
        sort_key = 'member__name'
        reverse_sort = False
    else:
        sort_key = 'klimapunkte'
        reverse_sort = True

    #members_with_klimapunkte_sortiert = sorted(members_with_klimapunkte, key=lambda x: x['klimapunkte'], reverse=True)
    try:
        members_with_klimapunkte_sortiert = sorted(
            members_with_klimapunkte,
            key=lambda x: x['member'].name if sort_key == 'member__name' else x[sort_key],
            reverse=reverse_sort
        )
    except KeyError:
        messages.error(request, "Fehler beim Sortieren der Mitglieder.")
        return redirect('family_detail', family_id)

    return render(request, './community_detail.html', {
        'community': community,
        'family': family,
        'members_with_klimapunkte': members_with_klimapunkte_sortiert,
        'zeitraum': zeitraum_text
    })


@login_required
def edit_community(request, community_id, family_id):
    community = get_community_or_redirect(request, community_id)
    family = get_family_or_redirect(request, family_id)
    if not community or not family:
        return redirect('community_view')

    if request.user not in family.members.all():
        messages.error(request, all_messages["community__not_member_of_family"])
        return redirect('home')

    if request.method == 'POST':
        if 'change_communityname' in request.POST:
            handle_change_communityname(request, community)
        elif 'change_password' in request.POST:
            handle_change_password(request, community)
        elif 'change_admin_password' in request.POST:
            handle_change_admin_password(request, community)
        elif 'remove_member' in request.POST:
            handle_remove_member(request, community, family)
            return redirect('home')
        elif 'leave_community' in request.POST:
            handle_leave_community(request, community, family)
            return redirect('home')
        elif 'delete_community' in request.POST:
            handle_delete_community(request, community)
            return redirect('home')

    return render(request, 'edit_community.html', {"community": community, "family": family})

@login_required
def chat_community(request, community_id, family_id):
    community = get_community_or_redirect(request, community_id)
    family = get_family_or_redirect(request, family_id)
    if not community or not family:
        return redirect('community_view')

    if request.user not in family.members.all():
        messages.error(request, all_messages["community__not_member_of_family"])
        return redirect('home')

    if request.method == 'POST':
        msg = request.POST.get('message')
        CommunityChatMessage.objects.create(community=community, user=request.user, message=msg, family=family)
        notify_community_users(request, community, f'Neue Nachricht in Community {community.name} von Family {family.name} / User {request.user}: {msg}', exclude_user=request.user)
        return redirect('chat_community', community_id=community.id, family_id=family.id)

    msgs = CommunityChatMessage.objects.filter(community_id=community_id).select_related('user', 'family')
    return render(request, 'chat_community.html', {'community': community, 'msgs': msgs, 'family': family})

@login_required
def check_communityname(request):
    communityname = request.GET.get('communityname', None)
    exists = Community.objects.filter(name=communityname).exists()
    return JsonResponse({'exists': exists})
"""
@login_required
def create_community(request):
    if request.method == 'POST':
        community_name = request.POST.get('communityname')
        community_password = request.POST.get('community_password')
        community_admin_password = request.POST.get('community_admin_password')
        family_name = request.POST.get('familyname')
        family_admin_password = request.POST.get('family_admin_password')
        
        if not community_name or not community_password or not community_admin_password or not family_name or not family_admin_password:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('create_community')

        if Community.objects.filter(name=community_name).exists():
            messages.error(request, all_messages["community_exists"])
            return redirect('create_community')
        
        try:
            family = Family.objects.get(name=family_name)
            if not check_password(family_admin_password, family.admin_password):
                messages.error(request, all_messages["community__invalid_family_credentials"])
                return redirect('create_community')
        except Family.DoesNotExist:
            messages.error(request, all_messages["community__invalid_family_credentials"])
            return redirect('create_community')

        community = Community.objects.create(name=community_name, password=community_password, admin_password=community_admin_password)
        community.members.add(family)
        createBenachrichtigung(request, f'Du hast die Community {community.name} mit der Family {family.name} erstellt', request.user)
        for user_to_message in family.members.all():
            createBenachrichtigung(request, f'Die Family {family.name} ist der Community {community.name} beigetreten', user_to_message)
        messages.success(request, all_messages["community_created"])
        return redirect('communities_view')
    
    return render(request, './create_community.html')


@login_required
def join_community(request):
    if request.method == 'POST':
        community_name = request.POST.get('communityname')
        community_password = request.POST.get('community_password')
        family_name = request.POST.get('familyname')
        family_admin_password = request.POST.get('family_admin_password')
        
        if not community_name or not community_password or not family_name or not family_admin_password:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('join_community')
        
        try:
            family = Family.objects.get(name=family_name)
            if not check_password(family_admin_password, family.admin_password):
                messages.error(request, all_messages["community__invalid_family_credentials"])
                return redirect('join_community')
        except Family.DoesNotExist:
            messages.error(request, all_messages["community__invalid_family_credentials"])
            return redirect('join_community')

        try:
            community = Community.objects.get(name=community_name)
            if family in community.members.all():
                messages.error(request, all_messages["family_already_in_community"])
                return redirect('join_community')
            if check_password(community_password, community.password):
                for user_to_message in family.members.all():
                    createBenachrichtigung(request, f'Die Family {family.name} ist der Community {community.name} beigetreten', user_to_message)
                community.members.add(family)
                messages.success(request, all_messages["community_joined"].format(family=family, community=community))
                return redirect('communities_view')
            else:
                messages.error(request, all_messages["invalid_community_credentials"])
                return redirect('join_community')
        except Community.DoesNotExist:
            messages.error(request, all_messages["invalid_community_credentials"])
            return redirect('join_community')

    return render(request, './join_community.html')

@login_required
def communities_view(request):
    # Hole die IDs der Families des aktuellen Nutzers
    user_families = getFamiliesOfUser(request.user)

    # Verwende diese IDs zum Filtern der Communities
    communities = Community.objects.filter(members__id__in=user_families).distinct().order_by('name')

    communities_with_user_families = []

    for community in communities:
        families_in_community = community.members.all()  # alle Families in dieser Community
        families_user_belongs_to = families_in_community & user_families  # Schnittmenge
        communities_with_user_families.append({'community': community, 'families': families_user_belongs_to})

    return render(request, './communities.html', {'communities_with_user_families': communities_with_user_families})

@login_required
def edit_community(request, community_id, family_id):
    if not community_id:
        messages.error(request, all_messages["community_id_missing"])
        return redirect('community_view')
    try:
        community = Community.objects.get(id=community_id)
    except Community.DoesNotExist:
        messages.error(request, all_messages["community_not_found"])
        return redirect('community_view')

    if not family_id:
        messages.error(request, all_messages["community__family_id_missing"])
        return redirect('communities_view')
    try:
        family = Family.objects.get(id=family_id)
    except Family.DoesNotExist:
        messages.error(request, all_messages["community__family_not_found"])
        return redirect('communities_view')

    if request.user not in family.members.all():
        messages.error(request, all_messages["community__not_member_of_family"])
        return redirect('home')

    if request.method == 'POST':

        if 'change_communityname' in request.POST:
            admin_password = request.POST.get('admin_password')
            communityname = request.POST.get('new_communityname')

            if not admin_password or not communityname:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                old_communityname = community.name
                community.name = communityname
                community.save()
                messages.success(request, all_messages["community_name_changed"])
                for user_to_message in community.user_members():
                    createBenachrichtigung(request, f'Der Communityname der Community {old_communityname} wurde zu {communityname} geändert', user_to_message)

        if 'change_password' in request.POST:
            admin_password = request.POST.get('admin_password')
            password = request.POST.get('new_password')

            if not admin_password or not password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                community.password = password
                community.save()
                for user_to_message in community.user_members():
                    createBenachrichtigung(request, f'Das Passwort der Community {community.name} wurde geändert', user_to_message)
                messages.success(request, all_messages["community_password_changed"])

        if 'change_admin_password' in request.POST:
            current_admin_password = request.POST.get('current_admin_password')
            new_admin_password = request.POST.get('new_admin_password')

            if not current_admin_password or not new_admin_password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(current_admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_passord"])
            else:
                community.admin_password = new_admin_password
                community.save()
                for user_to_message in community.user_members()():
                    createBenachrichtigung(request, f'Das Admin-Passwort der Community {community.name} wurde geändert', user_to_message)
                messages.success(request, all_messages["community_admin_password_changed"])
        
        if 'remove_member' in request.POST:
            admin_password = request.POST.get('admin_password')
            family_name = request.POST.get('family_name')

            if not admin_password or not family_name:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            elif family_name == family.name:
                community.members.remove(family)
                for user_to_message in community.user_members():
                    createBenachrichtigung(request, f'Die Family {family.name} wurde von {request.user} aus der Community {community.name} entfernt', user_to_message)
                messages.success(request, all_messages["family_left_community"])
                return redirect('home')
            else:
                family_to_remove = Family.objects.get(name=family_name)
                community = Community.objects.get(id=community_id)
                community.members.remove(family_to_remove)
                for user_to_message in community.user_members():
                    createBenachrichtigung(request, f'Die Family {family.name} wurde von {request.user} aus der Community {community.name} entfernt', user_to_message)
                messages.success(request, all_messages["community__family_removed"])
        
        if 'leave_community' in request.POST:
            family_admin_password = request.POST.get('family_admin_password')
            if not family_admin_password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(family_admin_password, family.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                community.members.remove(family)
                for user_to_message in community.user_members():
                    createBenachrichtigung(request, f'Die Family {family.name} wurde von {request.user} aus der Community {community.name} entfernt', user_to_message)
                messages.success(request, all_messages["family_left_community"])
                return redirect('home')

        if 'delete_community' in request.POST:
            admin_password = request.POST.get('admin_password')

            if not admin_password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                community.delete()
                for user_to_message in community.user_members():
                    createBenachrichtigung(request, f'Die Community {community.name} wurde von {request.user} gelöscht', user_to_message)
                messages.success(request, all_messages["community_deleted"])
                return redirect('home')

    return render(request, 'edit_community.html', {"community": community, "family": family})

@login_required
def chat_community(request, community_id, family_id):
    if not community_id:
        messages.error(request, all_messages["community_id_missing"])
        return redirect('community_view')
    try:
        community = Community.objects.get(id=community_id)
    except Community.DoesNotExist:
        messages.error(request, all_messages["community_not_found"])
        return redirect('community_view')

    if not family_id:
        messages.error(request, all_messages["community__family_id_missing"])
        return redirect(communities_view)
    try:
        family = Family.objects.get(id=family_id)
    except Family.DoesNotExist:
        messages.error(request, all_messages["community__family_not_found"])
        return redirect(communities_view)

    if request.user not in family.members.all():
        messages.error(request, all_messages["community__not_member_of_family"])
        return redirect('home')
    
    if request.method == 'POST':
        msg = request.POST.get('message')
        CommunityChatMessage.objects.create(community=community, user=request.user, message=msg, family=family)
        for user_to_message in community.user_members():
            if user_to_message != request.user:
                createBenachrichtigung(request, f'Neue Nachricht in Community {community.name} von Family {family.name} / User {request.user}: {msg}', user_to_message)
        return redirect('chat_community', community_id=community.id, family_id=family.id)
    
    #try:
    msgs = CommunityChatMessage.objects.filter(community_id=community_id)
    #except CommunityChatMessage.DoesNotExist:
    #    messages.error(request, all_messages["no_messages_found"])
    #    return redirect('chat_community')

    return render(request, 'chat_community.html', {'community': community, 'msgs': msgs, 'family': family})

def community_detail(request, community_id, family_id):
    if not community_id:
        messages.error(request, all_messages["community_id_missing"])
        return redirect('communities_view')
    try:
        community = Community.objects.get(id=community_id)
    except Community.DoesNotExist:
        messages.error(request, all_messages["community_not_found"])
        return redirect('home')
    
    if not family_id:
        messages.error(request, all_messages["community__family_id_missing"])
        return redirect('communities_view')
    try:
        family = Family.objects.get(id=family_id)
    except Family.DoesNotExist:
        messages.error(request, all_messages["community__family_not_found"])
        return redirect('communities_view')

    if request.user not in family.members.all():
        messages.error(request, all_messages["community__not_member_of_family"])
        return redirect('home')

    members_with_klimapunkte = []
    community_members = community.members.all()

    zeitraum = 'gesamt'

    if request.method == 'POST':
        filter = request.POST.get('filter')
        if filter not in ["Klimapunkte", "Familyname"]:
            messages.error(request, "Ungültiger Filter-Typ")
            return redirect('community_detail', community_id, family_id)

        zeitraum = request.POST.get('zeitraum')

        heute = date.today()
        siebenTage = heute - timedelta(days=7)
        dreißigTage = heute - timedelta(days=30)
        dreihundertfünfundsechzigTage = heute - timedelta(days=365)

        if zeitraum == 'benutzerdefiniert':
            start_datum = request.POST.get('start_date')
            end_datum = request.POST.get('end_date')

            if not start_datum or not end_datum:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('community_detail')

            try:
                start_datum = datetime.strptime(start_datum, '%Y-%m-%d').date()
                end_datum = datetime.strptime(end_datum, '%Y-%m-%d').date()

                if start_datum > end_datum or end_datum > heute:
                    messages.error(request, all_messages["invalid_date_range"])
                    return redirect('community_detail')
                if end_datum > heute:
                    messages.error(request, all_messages["date_in_future"])
                    return redirect('community_detail')

            except ValueError:
                messages.error(request, all_messages["invalid_date"])
                return redirect('community_detail')

            zeitraum_text = f'von {start_datum} bis {end_datum}'

        elif zeitraum not in ['heute', 'sieben Tage', 'dreißig Tage', 'dreihundertfünfundsechzig Tage', 'gesamt']:
            messages.error(request, all_messages["invalid_time_period"])
            return redirect('community_detail')
        
        
        for community_member in community_members:
            family_members = community_member.members.all()

            if zeitraum == 'heute':
                klimapunkte_gesamt = 0
                for single_member in family_members:
                    aktionen = Aktion.objects.filter(user=single_member, date=heute)
                    klimapunkte = get_klimapunkte(aktionen)
                    klimapunkte_gesamt += klimapunkte

                klimapunkte = klimapunkte_gesamt / community_member.member_count() if community_member.member_count() else 0

            elif zeitraum == 'sieben Tage':
                klimapunkte_gesamt = 0
                for single_member in family_members:
                    aktionen = Aktion.objects.filter(user=single_member, date__gte=siebenTage)
                    klimapunkte = get_klimapunkte(aktionen)
                    klimapunkte_gesamt += klimapunkte
                
                klimapunkte = klimapunkte_gesamt / community_member.member_count() if community_member.member_count() else 0

            elif zeitraum == 'dreißig Tage':
                klimapunkte_gesamt = 0
                for single_member in family_members:
                    aktionen = Aktion.objects.filter(user=single_member, date__gte=dreißigTage)
                    klimapunkte = get_klimapunkte(aktionen)
                    klimapunkte_gesamt += klimapunkte
                
                klimapunkte = klimapunkte_gesamt / community_member.member_count() if community_member.member_count() else 0

            elif zeitraum == 'dreihundertfünfundsechzig Tage':
                klimapunkte_gesamt = 0
                for single_member in family_members:
                    aktionen = Aktion.objects.filter(user=single_member, date__gte=dreihundertfünfundsechzigTage)
                    klimapunkte = get_klimapunkte(aktionen)
                    klimapunkte_gesamt += klimapunkte
                
                klimapunkte = klimapunkte_gesamt / community_member.member_count() if community_member.member_count() else 0


            elif zeitraum == 'gesamt':
                klimapunkte_gesamt = 0
                for single_member in family_members:
                    aktionen = Aktion.objects.filter(user=single_member)
                    klimapunkte = get_klimapunkte(aktionen)
                    klimapunkte_gesamt += klimapunkte
                
                klimapunkte = klimapunkte_gesamt / community_member.member_count() if community_member.member_count() else 0

            elif zeitraum == 'benutzerdefiniert':
                klimapunkte_gesamt = 0
                for single_member in family_members:
                    aktionen = Aktion.objects.filter(user=single_member, date__gte=dreißigTage)
                    klimapunkte = get_klimapunkte(aktionen)
                    klimapunkte_gesamt += klimapunkte
                
                klimapunkte = klimapunkte_gesamt / family_members.member_count() if family_members.member_count() else 0
                zeitraum = zeitraum_text
            
            if klimapunkte is None:
                klimapunkte = 0
   
            members_with_klimapunkte.append({'member': community_member, 'klimapunkte': klimapunkte, 'family_members': family_members})

    else:
        filter = "Klimapunkte"
        for community_member in community_members:
            family_members = community_member.members.all()
            klimapunkte_gesamt = 0
            for single_member in family_members:
                aktionen = Aktion.objects.filter(user=single_member)
                klimapunkte = get_klimapunkte(aktionen)
                klimapunkte_gesamt += klimapunkte
            
            community_members_count = community_member.member_count()
            klimapunkte = klimapunkte_gesamt / community_members_count if community_members_count else 0
            members_with_klimapunkte.append({'member': community_member, 'klimapunkte': klimapunkte, 'family_members': family_members})

    if filter == "Klimapunkte":
        sort_key = 'klimapunkte'
        reverse_sort = True
    elif filter == "Familyname":
        sort_key = 'member__name'  # oder 'member.username', je nach Struktur
        reverse_sort = False
    else:
        sort_key = 'klimapunkte'
        reverse_sort = True

    print(members_with_klimapunkte)
    # Sortierung anwenden
    try:
        members_with_klimapunkte_sortiert = sorted(
            members_with_klimapunkte,
            key=lambda x: x['member'].name if sort_key == 'member__name' else x[sort_key],
            reverse=reverse_sort
        )
    except KeyError:
        messages.error(request, "Fehler beim Sortieren der Mitglieder.")
        return redirect('family_detail', family_id)

    return render(request, './community_detail.html', {'community': community, 'family': family, 'members_with_klimapunkte': members_with_klimapunkte_sortiert, 'zeitraum': zeitraum, 'filter': filter})

@login_required
def check_communityname(request):
    communityname = request.GET.get('communityname', None)
    exists = Community.objects.filter(name=communityname).exists()
    return JsonResponse({'exists': exists})