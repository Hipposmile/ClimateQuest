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

from core.all_messages import all_messages
from .models import *
from utils.functions import *

from datetime import datetime, timedelta, date
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@login_required
def add(request):
    aktionen = AktionenListe.objects.all().order_by('name')

    if request.method == 'POST':
        is_truth = request.POST.get('is_truth') == 'on'
        if not is_truth:
            messages.error(request, all_messages["not_is_truth"])
            return redirect('add')

        action_type = request.POST.get('action_type')
        if not action_type:
            messages.error(request, all_messages["action_name_missing"])
            return redirect('add')
        
        action = AktionenListe.objects.get(name=action_type)
        action_description = request.POST.get('action_description')
        
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

        action_quantity = request.POST.get('action_quantity')
        if not action_quantity:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('add')
        try:
            action_quantity = float(action_quantity)
            rounded_action_quantity = round(action_quantity, dezimalstellen)
            action_quantity = rounded_action_quantity
        except ValueError:
            messages.error(request, all_messages["action_invalid_quantity"])
            return redirect('add')
        if action_quantity < 0:
            messages.error(request, all_messages["invalid_quantity"])
            return redirect('add')
        
        aktionExisting = any(aktion.name == action_type for aktion in aktionen)
        if not aktionExisting:
            messages.error(request, all_messages["invalid_action_type"])
            return redirect('add')
        
        old_level = get_level(request.user)

        Aktion.objects.create(
            aktion=action,
            description=action_description,
            user=request.user,
            quantity=action_quantity,
            date=action_date,
        )
        
        new_level = get_level(request.user)
        if old_level['level_number'] < new_level['level_number']:
            createBenachrichtigung(request, f'Du hast eine neue Aktion vom Typen {action_type} erstellt und bist so ins Level {new_level["current_level"].description} aufgestiegen. <p class="emoji">&#129395;</p>', request.user)
        else:
            createBenachrichtigung(request, f'Du hast eine neue Aktion vom Typen {action_type} erstellt.', request.user)

        messages.success(request, all_messages["action_added"])
        return redirect('history')

    return render(request, './add.html', {'aktionen': aktionen})

@login_required
def history(request):
    actions = Aktion.objects.filter(user=request.user).order_by('-date')
    return render(request, './history.html', {'actions': actions})

@login_required
def edit_action(request, action_id):
    if not action_id:
        messages.error(request, all_messages["action_id_missing"])
        return redirect('history')
    try:
        aktuelleAktion = Aktion.objects.get(id=action_id, user=request.user)
    except Aktion.DoesNotExist:
        messages.error(request, all_messages["action_not_found"])
        return redirect('history')
    
    aktionen = AktionenListe.objects.all().order_by('name')  

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
            
            action = AktionenListe.objects.get(name=action_type)
            action_description = request.POST.get('action_description')
            
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

            action_quantity = request.POST.get('action_quantity')
            if not action_quantity:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('edit_action', action_id)
            try:
                action_quantity = float(action_quantity)
                rounded_action_quantity = round(action_quantity, dezimalstellen)
                action_quantity = rounded_action_quantity
            except ValueError:
                messages.error(request, all_messages["invalid_quantity"])
                return redirect('edit_action', action_id)
            if action_quantity <= 0:
                messages.error(request, all_messages["invalid_quantity"])
                return redirect('edit_action', action_id)
            
            aktionExisting = any(aktion.name == action_type for aktion in aktionen)
            if not aktionExisting:
                messages.error(request, all_messages["invalid_action_type"])
                return redirect('edit_action', action_id)

            old_level = get_level(request.user)

            aktuelleAktion.aktion = action
            aktuelleAktion.description = action_description
            aktuelleAktion.user = request.user
            aktuelleAktion.quantity = action_quantity
            aktuelleAktion.date = action_date
            aktuelleAktion.save()

            new_level = get_level(request.user)
            if old_level['level_number'] < new_level['level_number']:
                createBenachrichtigung(request, f'Du hast eine Aktion vom Typen {action_type} bearbeitet und bist so ins Level {new_level["current_level"].description} aufgestiegen. <p class="emoji">&#x1F973;</p>', request.user)
            elif old_level['level_number'] > new_level['level_number']:
                createBenachrichtigung(request, f'Du hast eine Aktion vom Typen {action_type} bearbeitet, hast dadurch Klimapunkte verloren und bist so ins Level {new_level["current_level"].description} abgestiegen. <p class="emoji">&#x1F622;</p>', request.user)
            else:
                createBenachrichtigung(request, f'Du hast eine Aktion vom Typen {action_type} bearbeitet', request.user)

            messages.success(request, all_messages["action_edited"])
            return redirect('history')
        
        if 'delete_action' in request.POST:
            old_level = get_level(request.user)
            action_type = aktuelleAktion.aktion.name
            aktuelleAktion.delete()
            new_level = get_level(request.user)
            if old_level['level_number'] > new_level['level_number']:
                createBenachrichtigung(request, f'Du hast eine Aktion vom Typen {action_type} gelöscht, hast dadurch Klimapunkte verloren und bist so ins Level {new_level["current_level"].description} abgestiegen. <p class="emoji">&#x1F622;</p>', request.user)
            else:
                createBenachrichtigung(request, f'Du hast eine Aktion vom Typen {action_type} gelöscht', request.user)
            messages.success(request, all_messages["action_deleted"])
            return redirect('history')

    return render(request, './edit_action.html', {'aktionen': aktionen, 'aktuelleAktion': aktuelleAktion})
