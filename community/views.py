from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _
from core.all_messages import all_messages
from .models import Community, CommunityChatMessage
from family.models import Family
from aktionen.models import Aktion

from utils.functions import create_notification, get_families_of_user, get_klimapunkte, get_additional_klimapunkte, get_date_range


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

        if len(community_name) > 100 or len(community_password) > 100 or len(community_password) > 100:
            messages.error(request, all_messages["too_short_input"])

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

        community = Community.objects.create(name=community_name, password=community_password,
                                             admin_password=community_admin_password)
        community.members.add(family)
        for user_to_message in family.members.all().exclude(id=request.user.id):
            create_notification(request,
                                f'Die Family {family.name}, in der auch du Mitglied bist, ist der Community {community.name} beigetreten',
                                f'The family {family.name}, of which you are also a member, has joined the community {community.name}',
                                user_to_message,
                                url=reverse('community_detail',
                                            kwargs={'community_id': community.id, 'family_id': family.id}))
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
                for user_to_message in family.members.all().exclude(id=request.user.id):
                    create_notification(request,
                                        f'Die Family {family.name}, in der auch du Mitglied bist, ist der Community {community.name} beigetreten',
                                        f'The family {family.name}, of which you are also a member, has joined the community {community.name}',
                                        user_to_message,
                                        url=reverse('community_detail',
                                                    kwargs={'community_id': community.id, 'family_id': family.id}))
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
    user_families = get_families_of_user(request.user)

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
        return redirect('dashboard')

    if request.method == 'POST':

        if 'change_communityname' in request.POST:
            admin_password = request.POST.get('admin_password_communityname')
            communityname = request.POST.get('new_communityname')

            if len(communityname) > 100:
                messages.error(request, all_messages["too_long_input"])
                return redirect('edit_family', community_id, family_id)

            if Community.objects.filter(name=communityname).exists():
                messages.error(request, all_messages["community_exists"])
                return redirect('edit_community', community_id, family_id)

            if not admin_password or not communityname:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                old_communityname = community.name
                community.name = communityname
                community.save()
                messages.success(request, all_messages["community_name_changed"])
                for user_to_message in community.user_members().exclude(id=request.user.id):
                    user_to_message_family_id = Family.objects.filter(community__id=community.id,
                                                                      members=user_to_message).first().id
                    create_notification(request,
                                        f'Der Communityname der Community {old_communityname} wurde von {request.user} zu {communityname} geändert',
                                        f'The communitynma of the community {old_communityname} has been updated by {request.user} to {communityname}',
                                        user_to_message,
                                        url=reverse('community_detail', kwargs={'community_id': community.id,
                                                                                'family_id': user_to_message_family_id}) if user_to_message_family_id else None
                                        )

        if 'change_password' in request.POST:
            admin_password = request.POST.get('admin_password_password')
            password = request.POST.get('new_password')

            if len(password) > 100:
                messages.error(request, all_messages["too_long_input"])
                return redirect('edit_community', community_id, family_id)

            if not admin_password or not password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                community.password = password
                community.save()
                for user_to_message in community.user_members().exclude(id=request.user.id):
                    user_to_message_family_id = Family.objects.filter(community__id=community.id,
                                                                      members=user_to_message).first().id
                    create_notification(request,
                                        f'Das Passwort der Community {community.name} wurde von {request.user} geändert.',
                                        f'The password of the community {community.name} has been updated by {request.user}.',
                                        user_to_message,
                                        url=reverse('community_detail', kwargs={'community_id': community.id,
                                                                                'family_id': user_to_message_family_id}) if user_to_message_family_id else None
                                        )
                messages.success(request, all_messages["community_password_changed"])

        if 'change_admin_password' in request.POST:
            current_admin_password = request.POST.get('current_admin_password')
            new_admin_password = request.POST.get('new_admin_password')

            if len(new_admin_password) > 100:
                messages.error(request, all_messages["too_long_input"])
                return redirect('edit_community', community_id, family_id)

            if not current_admin_password or not new_admin_password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(current_admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                community.admin_password = new_admin_password
                community.save()
                for user_to_message in community.user_members().exclude(id=request.user.id):
                    user_to_message_family_id = Family.objects.filter(community__id=community.id,
                                                                      members=user_to_message).first().id
                    create_notification(request,
                                        f'Das Admin-Passwort der Community {community.name} wurde von {request.user} geändert',
                                        f'The admin-password of the community {community.name} has been updated by {request.user}.',
                                        user_to_message,
                                        url=reverse('community_detail', kwargs={'community_id': community.id,
                                                                                'family_id': user_to_message_family_id}) if user_to_message_family_id else None
                                        )
                messages.success(request, all_messages["community_admin_password_changed"])

        if 'remove_member' in request.POST:
            admin_password = request.POST.get('admin_password_remove')
            family_name = request.POST.get('family_name')

            if not admin_password or not family_name:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            elif family_name == family.name:
                community.members.remove(family)
                for user_to_message in community.user_members().exclude(id=request.user.id):
                    user_to_message_family_id = Family.objects.filter(community__id=community.id,
                                                                      members=user_to_message).first().id
                    create_notification(request,
                                        f'Die Family {family.name} wurde von {request.user} aus der Community {community.name} entfernt',
                                        f'The family {family.name} has been removed from the community {community.name} by {request.user}.',
                                        user_to_message,
                                        url=reverse('community_detail', kwargs={'community_id': community.id,
                                                                                'family_id': user_to_message_family_id}) if user_to_message_family_id else None
                                        )
                messages.success(request, all_messages["family_left_community"])
                return redirect('dashboard')
            else:
                try:
                    family_to_remove = Family.objects.get(name=family_name)
                except Family.DoesNotExist:
                    messages.error(request, all_messages["community__family_not_found"])
                    return redirect('edit_community', community_id, family_id)
                community = Community.objects.get(id=community_id)
                community.members.remove(family_to_remove)
                for user_to_message in community.user_members().exclude(id=request.user.id):
                    user_to_message_family_id = Family.objects.filter(community__id=community.id,
                                                                      members=user_to_message).first().id
                    create_notification(request,
                                        f'Die Family {family.name} wurde von {request.user} aus der Community {community.name} entfernt',
                                        f'The family {family.name} has been removed from the community {community.name} by {request.user}.',
                                        user_to_message,
                                        url=reverse('community_detail', kwargs={'community_id': community.id,
                                                                                'family_id': user_to_message_family_id}) if user_to_message_family_id else None
                                        )
                messages.success(request, all_messages["community__family_removed"])

        if 'leave_community' in request.POST:
            family_admin_password = request.POST.get('family_admin_password')
            if not family_admin_password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(family_admin_password, family.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                community.members.remove(family)
                for user_to_message in community.user_members().exclude(id=request.user.id):
                    user_to_message_family_id = Family.objects.filter(community__id=community.id,
                                                                      members=user_to_message).first().id
                    create_notification(request,
                                        f'Die Family {family.name} wurde von {request.user} aus der Community {community.name} entfernt',
                                        f'The family {family.name} has been removed from the community {community.name} by {request.user}.',
                                        user_to_message,
                                        url=reverse('community_detail', kwargs={'community_id': community.id,
                                                                                'family_id': user_to_message_family_id}) if user_to_message_family_id else None
                                        )
                messages.success(request, all_messages["family_left_community"])
                return redirect('dashboard')

        if 'change_chat_settings' in request.POST:
            admin_password = request.POST.get('admin_password_chat_settings')
            if not check_password(admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                chat_enabled = request.POST.get('chat_checkbox') == 'on'
                community.chat = chat_enabled
                community.save()
                if chat_enabled:
                    messages.success(request, all_messages["community_chat_enabled"])
                else:
                    messages.success(request, all_messages["community_chat_disabled"])

        if 'delete_community' in request.POST:
            admin_password = request.POST.get('admin_password_delete')

            if not admin_password:
                messages.error(request, all_messages["missing_required_inputs"])
            elif not check_password(admin_password, community.admin_password):
                messages.error(request, all_messages["invalid_admin_password"])
            else:
                for user_to_message in community.user_members():
                    user_to_message_family_id = Family.objects.filter(community__id=community.id,
                                                                      members=user_to_message).first().id
                    create_notification(request, f'Die Community {community.name} wurde von {request.user} gelöscht',
                                        f'The community {community.name} has been deleted by {request.user}.',
                                        user_to_message,
                                        url=reverse('community_detail', kwargs={'community_id': community.id,
                                                                                'family_id': user_to_message_family_id}) if user_to_message_family_id else None
                                        )
                community.delete()
                messages.success(request, all_messages["community_deleted"])
                return redirect('dashboard')

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

    if not community.chat:
        messages.error(request, all_messages["chat_disabled_for_community"])
        return redirect('community_detail', community_id=community_id, family_id=family_id)

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
        return redirect('dashboard')

    if request.method == 'POST':
        msg = request.POST.get('message')
        CommunityChatMessage.objects.create(community=community, user=request.user, message=msg, family=family)
        for user_to_message in community.user_members().exclude(id=request.user.id):
            user_to_message_family_id = Family.objects.filter(community__id=community.id,
                                                              members=user_to_message).first().id
            create_notification(request,
                                f'Neue Nachricht in Community {community.name} von Family {family.name} / User {request.user}: {msg}',
                                f'New message in community {community.name} / User {request.user}: {msg}',
                                user_to_message,
                                url=reverse('community_detail', kwargs={'community_id': community.id,
                                                                        'family_id': user_to_message_family_id}) if user_to_message_family_id else None
                                )
        return redirect('chat_community', community_id=community.id, family_id=family.id)

    msgs = CommunityChatMessage.objects.filter(community_id=community_id)

    return render(request, 'chat_community.html', {'community': community, 'msgs': msgs, 'family': family})


VALID_ZEITRAEUME = {'Heute', 'Sieben Tage', 'Dreißig Tage', 'Dreihundertfünfundsechzig Tage', 'Gesamt',
                    'Benutzerdefiniert'}


@login_required
def community_detail(request, community_id, family_id):
    if not community_id:
        messages.error(request, all_messages["community_id_missing"])
        return redirect('communities_view')
    try:
        community = Community.objects.get(id=community_id)
    except Community.DoesNotExist:
        messages.error(request, all_messages["community_not_found"])
        return redirect('dashboard')

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
        return redirect('communities_view')

    heute = date.today()
    zeitraum_text = _("Gesamt")
    start_datum = end_datum = None

    if request.method == 'POST':
        zeitraum = request.POST.get('zeitraum', 'Gesamt')

        if zeitraum not in VALID_ZEITRAEUME:
            messages.error(request, all_messages["invalid_time_period"])
            return redirect('community_detail', community_id, family_id)

        if zeitraum == 'Benutzerdefiniert':
            raw_start = request.POST.get('start_date')
            raw_end = request.POST.get('end_date')

            if not raw_start or not raw_end:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('community_detail', community_id, family_id)

            try:
                start_datum = datetime.strptime(raw_start, '%Y-%m-%d').date()
                end_datum = datetime.strptime(raw_end, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, all_messages["invalid_date"])
                return redirect('community_detail', community_id, family_id)

            if start_datum > end_datum:
                messages.error(request, all_messages["invalid_date_range"])
                return redirect('community_detail', community_id, family_id)
            if end_datum > heute:
                messages.error(request, all_messages["date_in_future"])
                return redirect('community_detail', community_id, family_id)

            zeitraum_text = _("%(start)s bis %(end)s") % {
                'start': start_datum.strftime('%d.%m.%Y') if request.LANGUAGE_CODE == 'de' else start_datum.strftime(
                    '%m/%d/%Y'),
                'end': end_datum.strftime('%d.%m.%Y') if request.LANGUAGE_CODE == 'de' else end_datum.strftime(
                    '%m/%d/%Y'),
            }
        else:
            start_datum, end_datum = get_date_range(zeitraum, heute)

            if zeitraum == 'Heute':
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

    community_members = community.members.all()
    members_with_klimapunkte = []

    for community_member in community_members:
        family_members = community_member.members.all()
        klimapunkte_gesamt = 0
        for single_member in family_members:
            aktionen = Aktion.objects.filter(user=single_member)
            if start_datum and end_datum:
                aktionen = aktionen.filter(date__range=(start_datum, end_datum))
            klimapunkte = get_klimapunkte(aktionen)
            klimapunkte += get_additional_klimapunkte(single_member)
            klimapunkte_gesamt += klimapunkte

        community_members_count = community_member.member_count()
        klimapunkte = klimapunkte_gesamt / community_members_count if community_members_count else 0

        if klimapunkte is None:
            klimapunkte = 0

        members_with_klimapunkte.append(
            {'member': community_member, 'klimapunkte': klimapunkte})

    # Sortierung anwenden
    try:
        members_with_klimapunkte_sortiert = sorted(
            members_with_klimapunkte,
            key=lambda x: x['klimapunkte'],
            reverse=True
        )
    except KeyError:
        messages.error(request, _("Fehler beim Sortieren der Mitglieder."))
        return redirect('community_detail', community_id, family_id)

    return render(request, './community_detail.html', {'community': community, 'family': family,
                                                       'members_with_klimapunkte': members_with_klimapunkte_sortiert,
                                                       'zeitraum': zeitraum_text})


@login_required
def check_communityname(request):
    communityname = request.GET.get('communityname', None)
    exists = Community.objects.filter(name=communityname).exists()
    return JsonResponse({'exists': exists})
