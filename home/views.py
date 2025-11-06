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
import os
from django.core.management import call_command
from django.contrib.auth.models import User
from django.utils import timezone
from .models import *
from events.models import *
from utils.functions import *
import os
from utils.functions import *
from dotenv import load_dotenv

load_dotenv()

from core.all_messages import all_messages

from datetime import datetime, timedelta, date
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def home(request):
    klimapunkte_gesamt = 0
    user_count = 0
    for user in User.objects.prefetch_related():
        aktionen = Aktion.objects.filter(user=user)
        klimapunkte = get_klimapunkte(aktionen)
        klimapunkte_gesamt += klimapunkte
        user_count += 1
    return render(request, './home.html', {'klimapunkte': klimapunkte_gesamt, 'user_count': user_count})

@login_required
def admin(request):
    if not request.user.is_staff:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect('home')
    if request.method == 'POST':
        if 'benachrichtigung' in request.POST:
            receiver = request.POST.get('receiver')
            name = request.POST.get('name')
            msg = request.POST.get('msg')

            if not receiver or not name or not msg:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('admin')
            
            if receiver == 'user':
                try:
                    user = User.objects.get(username=name)
                    createBenachrichtigung(request, msg, user)
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
                    createBenachrichtigung(request, msg, user)
                messages.success(request, all_messages["admin__successfully_sent_notification"])
            elif receiver == 'community-members':
                try:
                    community = Community.objects.get(name=name)
                except Community.DoesNotExist:
                    messages.error(request, all_messages["admin__community_not_found"])
                    return redirect('admin')
                for family in community.members.all():
                    for user in family.members.all():
                        createBenachrichtigung(request, msg, user)
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
                    createBenachrichtigung(request, msg, participant)
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

def aktionenTable(request):
    aktionen = AktionenListe.objects.all()
    print(aktionen)
    return render(request, 'aktionenTable.html', {'aktionen': aktionen})

def datenschutz(request):
    return render(request, 'datenschutz.html')

def impressum(request):
    return render(request, 'impressum.html')
