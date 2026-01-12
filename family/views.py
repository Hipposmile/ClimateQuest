from datetime import datetime, timedelta, date

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.all_messages import all_messages
from utils.functions import *
from aktionen.models import *
from .models import *


@login_required
def create_family(request):
    if request.method == 'POST':
        family_name = request.POST.get('familyname')
        family_password = request.POST.get('family_password')
        family_admin_password = request.POST.get('family_admin_password')
        
        if not family_name or not family_password or not family_admin_password:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('create_family')

        if len(family_name) > 100 or len(family_password) > 100 or len(family_admin_password) > 100:
            messages.error(request, all_messages["too_long_input"])
            return redirect('create_family')

        if Family.objects.filter(name=family_name).exists():
            messages.error(request, all_messages["family_exists"])
            return redirect('create_family')
        
        if family_name == 'worldwide ranking':
            messages.error(request, all_messages["family_name_forbidden"])
            return redirect('create_family')

        family = Family.objects.create(name=family_name, password=family_password, admin_password=family_admin_password)
        family.members.add(request.user)
        messages.success(request, all_messages["family_created"])
        return redirect('families_view')
    
    return render(request, './create_family.html')

@login_required
def join_family(request):
    if request.method == 'POST':
        family_name = request.POST.get('familyname')
        family_password = request.POST.get('family_password')
        if not family_name or not family_password:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('join_family')

        try:
            family = Family.objects.get(name=family_name)
            if request.user in family.members.all():
                messages.error(request, all_messages["family_already_joined"])
            if check_password(family_password, family.password):
                for user_to_message in family.members.all().exclude(id=request.user.id):
                    create_notification(request, f'User {request.user} ist der Family {family} beigetreten', user_to_message)
                family.members.add(request.user)
                messages.success(request, all_messages["family_joined"].format(family=family))
                return redirect('families_view')
            else:
                messages.error(request, all_messages["invalid_family_credentials"])
                return redirect('join_family')
        except Family.DoesNotExist:
            messages.error(request, all_messages["invalid_family_credentials"])
            return redirect('join_family')

    return render(request, './join_family.html')

@login_required
def chat_family(request, family_id):
    if not family_id:
        messages.error(request, all_messages["family_id_missing"])
        return redirect('dashboard')
    try:
        family = Family.objects.get(id=family_id)
    except Family.DoesNotExist:
        messages.error(request, all_messages["family_not_found"])
        return redirect('dashboard')

    if family.name == 'worldwide ranking':
        messages.error(request, all_messages["chat_not_enabled_for_worldwide"])
        return redirect('dashboard')
    
    if not family.chat:
        messages.error(request, all_messages["chat_disabled_for_family"])
        return redirect('family_detail', family_id=family.id)

    if request.user not in family.members.all():
        messages.error(request, all_messages["not_part_of_family"].format(family=family))
        return redirect('dashboard')
    
    if request.method == 'POST':
        msg = request.POST.get('message')
        FamilyChatMessage.objects.create(family=family, user=request.user, message=msg)
        for user_to_message in family.members.all().exclude(id=request.user.id):
            if user_to_message != request.user:
                create_notification(request, f'Neue Nachricht in Family {family.name} von User {request.user}: {msg}', user_to_message)
        return redirect('chat_family', family_id=family.id)
    
    msgs = FamilyChatMessage.objects.filter(family=family)

    return render(request, 'chat_family.html', {'family': family, 'msgs': msgs})

@login_required
def families_view(request):
    check_worldwide_ranking_exists(request)
    families = get_families_of_user(request.user)
    return render(request, './families.html', {'families': families})

@login_required
def edit_family(request, family_id):
    if not family_id:
        messages.error(request, all_messages["family_id_missing"])
        return redirect('dashboard')
    try:
        family = Family.objects.get(id=family_id)
    except Family.DoesNotExist:
        messages.error(request, all_messages["family_not_found"])
        return redirect('dashboard')

    if family.name == 'worldwide ranking':
        messages.error(request, all_messages["family_name_forbidden"])
        return redirect('dashboard')
    
    if request.user not in family.members.all():
        messages.error(request, all_messages["not_part_of_family"].format(family=family))
        return redirect('dashboard')

    if request.method == 'POST':
        if 'change_familyname' in request.POST:
            admin_password = request.POST.get('admin_password')
            familyname = request.POST.get('new_familyname')

            if Family.objects.filter(name=familyname).exists():
                messages.error(request, all_messages["family_exists"])
                return redirect('edit_family', family_id)

            if len(familyname) > 100:
                messages.error(request, all_messages["too_long_input"])
                return redirect('edit_family', family_id)

            if not admin_password or not familyname:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, family.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                old_familyname = family.name
                family.name = familyname
                family.save()
                for user_to_message in family.members.all().exclude(id=request.user.id):
                    create_notification(request, f'Der Familyname der Family {old_familyname} wurde von {request.user} zu {familyname} geändert', user_to_message)
                messages.success(request, all_messages["family_name_changed"])

        if 'change_password' in request.POST:
            admin_password = request.POST.get('admin_password')
            password = request.POST.get('new_password')

            if len(password) > 100:
                messages.error(request, all_messages["too_long_input"])
                return redirect('edit_family', family_id)

            if not admin_password or not password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, family.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                family.password = password
                family.save()
                for user_to_message in family.members.all().exclude(id=request.user.id):
                    create_notification(request, f'Passwort bei Family {family.name} wurde von User {request.user} geändert', user_to_message)
                messages.success(request, all_messages["family_password_changed"])

        if 'change_admin_password' in request.POST:
            current_admin_password = request.POST.get('current_admin_password')
            new_admin_password = request.POST.get('new_admin_password')

            if len(new_admin_password) > 100:
                messages.error(request, all_messages["too_long_input"])
                return redirect('edit_family', family_id)

            if not current_admin_password or not new_admin_password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(current_admin_password, family.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                family.admin_password = new_admin_password
                family.save()
                for user_to_message in family.members.all().exclude(id=request.user.id):
                    create_notification(request, f'Das Family-Admin-Passwort der Family {family.name} wurde von User {request.user} geändert', user_to_message)
                messages.success(request, all_messages["family_admin_password_changed"])
        
        if 'remove_member' in request.POST:
            admin_password = request.POST.get('admin_password')
            username = request.POST.get('username')

            if not admin_password or not username:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, family.admin_password):
                messages.error(request, all_messages["admin_password_invalid"])
            elif username == request.user.username:
                family.members.remove(request.user)
                messages.success(request, all_messages["family_left"])
                return redirect('dashboard')
            else:
                user = User.objects.get(username=username)
                family = Family.objects.get(id=family_id)
                family.members.remove(user)
                for user_to_message in family.members.all():
                    if user_to_message == user:
                        create_notification(request, f'Du wurdest von User {request.user} aus der Family {family.name} entfernt', user_to_message)
                    else:
                        create_notification(request, f'User {user} wurde von User {request.user} aus Family {family.name} entfernt.', user_to_message)
                messages.error(request, all_messages["family_user_removed"])
        
        if 'leave_family' in request.POST:
            family.members.remove(request.user)
            messages.success(request, all_messages["family_left"])
            return redirect('dashboard')

        if 'change_chat_settings' in request.POST:
            admin_password = request.POST.get('admin_password')
            if not check_password(admin_password, family.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                chat_enabled = request.POST.get('chat_checkbox') == 'on'
                family.chat = chat_enabled
                family.save()
                if chat_enabled:
                    messages.success(request, all_messages["family_chat_enabled"])
                else:
                    messages.success(request, all_messages["family_chat_disabled"])

        if 'delete_family' in request.POST:
            admin_password = request.POST.get('admin_password')
            if not admin_password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, family.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                for user_to_message in family.members.all().exclude(id=request.user.id):
                    create_notification(request, f'Family {family.name} wurde von User {request.user} gelöscht.', user_to_message)
                family.delete()
                messages.success(request, all_messages["family_deleted"])
                return redirect('dashboard')

    return render(request, 'edit_family.html', {'family': family})

@login_required
def family_detail(request, family_id):
    if not family_id:
        messages.error(request, all_messages["family_id_missing"])
        return redirect('dashboard')
    try:
        family = Family.objects.get(id=family_id)
    except Family.DoesNotExist:
        messages.error(request, all_messages["family_not_found"])
        return redirect('dashboard')
    
    members_with_klimapunkte = []
    members = family.members.all()

    zeitraum = 'gesamt'

    if request.method == 'POST':
        zeitraum = request.POST.get('zeitraum')

        heute = date.today()
        seven_days = heute - timedelta(days=7)
        thirty_days = heute - timedelta(days=30)
        threehundertsixtyfive_days = heute - timedelta(days=365)

        if zeitraum == 'benutzerdefiniert':
            start_datum = request.POST.get('start_date')
            end_datum = request.POST.get('end_date')

            if not start_datum or not end_datum:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('family_detail', family_id)

            try:
                start_datum = datetime.strptime(start_datum, '%Y-%m-%d').date()
                end_datum = datetime.strptime(end_datum, '%Y-%m-%d').date()

                if start_datum > end_datum or end_datum > heute:
                    messages.error(request, all_messages["invalid_date_range"])
                    return redirect('family_detail', family_id)
                if end_datum > heute:
                    messages.error(request, all_messages["date_in_future"])
                    return redirect('family_detail', family_id)

            except ValueError:
                messages.error(request, all_messages["invalid_date"])
                return redirect('family_detail', family_id)

            zeitraum_text = f"von {start_datum.strftime('%d.%m.%Y')} bis {end_datum.strftime('%d.%m.%Y')}"

        elif zeitraum not in ['heute', 'sieben Tage', 'dreißig Tage', 'dreihundertfünfundsechzig Tage', 'gesamt']:
            messages.error(request, all_messages["invalid_time_period"])
            return redirect('family_detail', family_id)
        
        for member in members:

            if zeitraum == 'heute':
                aktionen = Aktion.objects.filter(user=member, date=heute)
                klimapunkte = get_klimapunkte(aktionen)

            elif zeitraum == 'sieben Tage':
                aktionen = Aktion.objects.filter(user=member, date__gte=seven_days)
                klimapunkte = get_klimapunkte(aktionen)

            elif zeitraum == 'dreißig Tage':
                aktionen = Aktion.objects.filter(user=member, date__gte=thirty_days)
                klimapunkte = get_klimapunkte(aktionen)

            elif zeitraum == 'dreihundertfünfundsechzig Tage':
                aktionen = Aktion.objects.filter(user=member, date__gte=threehundertsixtyfive_days)
                klimapunkte = get_klimapunkte(aktionen)

            elif zeitraum == 'gesamt':
                aktionen = Aktion.objects.filter(user=member)
                klimapunkte = get_klimapunkte(aktionen)
                
            elif zeitraum == 'benutzerdefiniert':
                aktionen = Aktion.objects.filter(user=member, date__range=(start_datum, end_datum))
                klimapunkte = get_klimapunkte(aktionen)
                zeitraum = zeitraum_text
            
            if klimapunkte is None:
                klimapunkte = 0

            klimapunkte += get_klimapunkte_from_likes(member)
            members_with_klimapunkte.append({'member': member, 'klimapunkte': klimapunkte})

    else:
        for member in members:
            aktionen = Aktion.objects.filter(user=member)
            klimapunkte = get_klimapunkte(aktionen)
            klimapunkte += get_klimapunkte_from_likes(member)
            members_with_klimapunkte.append({'member': member, 'klimapunkte': klimapunkte})

    # Sortierung anwenden
    try:
        print(members_with_klimapunkte)
        members_with_klimapunkte_sortiert = sorted(
            members_with_klimapunkte,
            key=lambda x: x['klimapunkte'],
            reverse=True
        )
    except KeyError:
        messages.error(request, "Fehler beim Sortieren der Mitglieder.")
        return redirect('family_detail', family_id)

    total_klimapunkte = sum(member['klimapunkte'] for member in members_with_klimapunkte_sortiert)
    members_count = len(members_with_klimapunkte)
    average_klimapunkte = total_klimapunkte / members_count if members_with_klimapunkte_sortiert else 0
    return render(request, './family_detail.html', {
        'family': family,
        'members': members_with_klimapunkte_sortiert,
        'zeitraum': zeitraum,
        'average_klimapunkte': average_klimapunkte,
        'total_klimapunkte': total_klimapunkte,
        'members_count': members_count,
    })

@login_required
def check_familyname(request):
    familyname = request.GET.get('familyname', None)
    exists = Family.objects.filter(name=familyname).exists()
    return JsonResponse({'exists': exists})