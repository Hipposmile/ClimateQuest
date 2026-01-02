import os

import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from dotenv import load_dotenv

from core.all_messages import all_messages

load_dotenv()

from utils.functions import *

from django.utils.encoding import force_bytes
from .tokens import email_verification_token
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password


def generate_verification_link(request):
    user = request.user
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    activation_link = request.build_absolute_uri(
        reverse('activate', kwargs={'uidb64': uid, 'token': token})
    )
    return activation_link


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'home'
            return redirect(next_url)
        else:
            messages.error(request, all_messages["invalid_login_data"])
            return redirect('login_view')
    return render(request, './login.html', {'next': request.GET.get('next', '')})


def logout_view(request):
    logout(request)
    return redirect('home')

def register_view(request):
    if request.method == 'POST':
        # reCAPTCHA
        recaptcha_token = request.POST.get('recaptchaToken')
        if not recaptcha_token:
            messages.error(request, "reCAPTCHA-Token fehlt. Bitte versuche es erneut.")
            return redirect('register_view')
        recaptcha_secret = os.environ.get("RECAPTCHA_PRIVATE_KEY", "")

        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': recaptcha_secret,
                'response': recaptcha_token
            }
        )
        result = response.json()

        if not result.get('success') or result.get('score', 0) < 0.5:
            messages.error(request, all_messages["robot"])
            return redirect('register_view')

        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        nutzungsbedingungen_accepted = request.POST.get('nutzungsbedingungen_accepted') == 'on'

        if not nutzungsbedingungen_accepted:
            messages.error(request, all_messages["nutungsbedingungen_not_accepted"])
            return redirect('register_view')

        if User.objects.filter(username=username).exists():
            messages.error(request, all_messages["username_not_available"])
            return redirect('register_view')

        if email == "":
            user = User.objects.create_user(username=username, password=password)
            actions_after_registration(request, user)
            UserErweitert.objects.filter(user=user).update(mail_verified=True)
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, all_messages['successfully_signed_up_email_not_verified'])
                return redirect('dashboard')
            create_internal_error(request, 'bei Registrierung existiert Nutzer nicht')
            return redirect('register_view')

        if not ist_email_gueltig(email):
            messages.error(request, all_messages["invalid_email"])
            return redirect('register_view')

        if User.objects.filter(email=email).exists():
            messages.error(request, all_messages["email_not_available"])
            return redirect('register_view')

        user = User.objects.create_user(username=username, password=password, email=email)

        actions_after_registration(request, user)
        UserErweitert.objects.filter(user=user).update(mail_verified=False)
        user_authenticated = authenticate(username=username, password=password)
        if user_authenticated:
            login(request, user)
            messages.success(request, all_messages['successfully_signed_up'])
        else:
            create_internal_error(request, 'bei Registrierung existiert Nutzer nicht')
            return redirect('register_view')

        activation_link = generate_verification_link(request)

        send_mail_function(
            request=request,
            subject='ClimateQuest - dein Aktivierungslink ist da!',
            message=f'Bitte klick auf den folgenden Link, um deine E-Mail-Adresse zu verifizieren: {activation_link}',
            recipient_list=email,
            fail_silently=False,
            mailinglist_needless=True,
            user=user,
            fehlermeldung='Fehler beim E-Mail-Versand. Probiere die Registrierung ohne E-Mail und füge deine E-Mail-Adresse später in den Einstellungen hinzu.'
        )

        return redirect('dashboard')

    return render(request, './register.html')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
    except Exception:
        user = None

    if user and email_verification_token.check_token(user, token):
        UserErweitert.objects.filter(user=user).update(mail_verified=True)
        user.save()
        messages.success(request, all_messages["email_verified"])
        return redirect('dashboard')
    else:
        messages.error(request, all_messages["invalid_verification_link"])
        return redirect('dashboard')


@login_required
def resend_verification_email(request):
    if not request.user.is_authenticated:
        messages.error(request, all_messages["login_required"])
        return redirect('login_view')

    if request.user.email == "":
        messages.error(request, all_messages["no_email_to_verify"])
        return redirect('settings_view')

    activation_link = generate_verification_link(request)

    send_mail_function(
        request=request,
        subject='ClimateQuest - dein Aktivierungslink ist da!',
        message=f'Bitte klick auf den folgenden Link, um deine E-Mail-Adresse zu verifizieren: {activation_link}',
        recipient_list=request.user.email,
        fail_silently=False,
        mailinglist_needless=True,
        user=request.user,
        fehlermeldung='Fehler beim E-Mail-Versand. Probiere es später erneut.'
    )

    messages.success(request, all_messages["verification_email_resent"])
    return redirect('settings_view')


@login_required
def settings_view(request):
    if request.method == 'POST':
        if 'change_username' in request.POST:
            password = request.POST.get('password')
            new_username = request.POST.get('new_username')
            if not check_password(password, request.user.password):
                messages.error(request, all_messages["invalid_password"])
            else:
                if User.objects.filter(username=new_username).exists():
                    messages.error(request, all_messages["username_not_available"])
                elif new_username == request.user.username:
                    messages.error(request, all_messages["username_belongs_to_you"])
                else:
                    request.user.username = new_username
                    request.user.save()
                    create_notification(request, 'Du hast deinen Benutzernamen geändert.', request.user)
                    messages.success(request, all_messages["username_changed"])
            return redirect('settings_view')

        if 'change_password' in request.POST:
            current_pw = request.POST.get('current_password')
            new_pw = request.POST.get('new_password')
            if not request.user.check_password(current_pw):
                messages.error(request, all_messages["invalid_password"])
            else:
                request.user.set_password(new_pw)
                request.user.save()
                update_session_auth_hash(request, request.user)
                create_notification(request, 'Du hast dein Passwort geändert.', request.user)
                messages.success(request, all_messages["password_changed"])
            return redirect('settings_view')

        if 'change_email' in request.POST:
            email = request.POST.get('email')
            password = request.POST.get('password')
            if not request.user.check_password(password):
                messages.error(request, all_messages["invalid_password"])
            else:
                if email == "":
                    request.user.email = email
                    request.user.save()
                    create_notification(request, all_messages["successfully_changed_email_no_email"])
                    messages.success(request, all_messages["successfully_changed_email_no_email"])
                    return redirect('settings_view')

                if not ist_email_gueltig(email):
                    messages.error(request, all_messages["invalid_email"])
                    return redirect('settings_view')

                if User.objects.filter(email=email).exists():
                    messages.error(request, all_messages["email_not_available"])
                    return redirect('settings_view')

                old_email = request.user.email

                request.user.email = email
                request.user.save()
                UserErweitert.objects.filter(user=request.user).update(mail_verified=False)

                activation_link = generate_verification_link(request)

                mail_output = send_mail_function(
                    request=request,
                    subject='ClimateQuest - dein Aktivierungslink ist da!',
                    message=f'Bitte klick auf den folgenden Link, um deine E-Mail-Adresse zu verifizieren: {activation_link}',
                    recipient_list=email,
                    fail_silently=False,
                    mailinglist_needless=True,
                    user=request.user,
                )

                if not mail_output:
                    request.user.email = old_email
                    request.user.save()
                    UserErweitert.objects.filter(user=request.user).update(mail_verified=True)
                    return redirect('settings_view')
                else:
                    create_notification(request, "Du hast deine E-Mail Adresse geändert.")
                    messages.success(request, all_messages["email_changed"])
                return redirect('settings_view')

        if 'change_email_settings' in request.POST:
            mailinglist = request.POST.get('mailinglist') == 'on'
            password = request.POST.get('password')
            if not request.user.check_password(password):
                messages.error(request, all_messages["invalid_password"])
                return redirect('settings_view')
            try:
                user_erweitert = UserErweitert.objects.get(user=request.user)
            except UserErweitert.DoesNotExist:
                create_internal_error(request, f'UserErweitert zu User {request.user} existiert nicht')
            user_erweitert.mailinglist = mailinglist
            user_erweitert.save()
            if user_erweitert.mailinglist:
                messages.success(request, all_messages["mailinglist_enabled"])
            else:
                messages.success(request, all_messages["mailinglist_disabled"])
            create_notification(request, "Du hast deine Mail-Einstellungen geändert")
            return redirect('settings_view')

        if 'change_statement' in request.POST:
            statement = request.POST.get('statement')
            password = request.POST.get('password')
            if not request.user.check_password(password):
                messages.error(request, all_messages["invalid_password"])
                return redirect('settings_view')
            try:
                user_erweitert = UserErweitert.objects.get(user=request.user)
            except UserErweitert.DoesNotExist:
                create_internal_error(request, f'UserErweitert zu User {request.user} existiert nicht')
            user_erweitert.statement = statement
            user_erweitert.save()
            messages.success(request, all_messages["successfully_changed_statement"])
            create_notification(request, all_messages["successfully_changed_statement"])
            return redirect('settings_view')

        if 'delete_account' in request.POST:
            password = request.POST.get('password')
            if not request.user.check_password(password):
                messages.error(request, all_messages["invalid_password"])
            else:
                contacted_user_ids = set()
                families = get_families_of_user(request.user) or []
                communities = get_communities_of_user(request.user) or []
                for family in families:
                    if family.name != 'worldwide ranking':
                        for user in family.members.all():
                            if user.id not in contacted_user_ids:
                                contacted_user_ids.add(user.id)
                                create_notification(request,
                                                    f'User {request.user.username}, mit dem / der du zusammen in einer Family oder Community bist, hat den eigenen Account gelöscht. Von {request.user.username} gesendete Nachrichten werden auch gelöscht.',
                                                    user)
                for community in communities:
                    for family in community.members.all():
                        for user in family.members.all():
                            if user.id not in contacted_user_ids:
                                contacted_user_ids.add(user.id)
                                create_notification(request,
                                                    f'User {request.user.username}, mit dem du zusammen in einer Family oder Community bist, hat seinen Account gelöscht. Nachrichten von ihm werden auch gelöscht.',
                                                    user)
                request.user.delete()
                logout(request)
                messages.error(request, all_messages["account_deleted"])
                return redirect('login_view')

    return render(request, './personal_settings.html')


def reset_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, all_messages["email_not_found"])
            return redirect('reset_password')

        new_password = generate_random_password()

        output = send_mail_function(
            request=request,
            subject='ClimateQuest - Passwort Reset',
            message=f'Wir haben dir ein neues, zufällig generiertes Passwort erstellt: <b>{new_password}</b> \nMelde dich damit und mit deinem Benutzernamen <b>{user.username}</b> <a href="https://climate-quest.de/personals/login/">hier</a> an und ändere aus Sicherheitsgründen möglichst bald unter "Profil bearbeiten" dein Passwort.',
            recipient_list=user.email,
            fail_silently=False,
            user=user,
        )

        if output:
            try:
                user.set_password(new_password)
                user.save()
                create_notification(request, 'Du hast dein Passwort resettet.', user)
                messages.success(request, all_messages["password_reset_mail_sent"])
                return redirect('login_view')

            except Exception as e:
                create_internal_error(request, f'Fehler beim Zurücksetzen des Passworts: {e}',
                                      all_messages["password_reset_error"])
                return redirect('reset_password')
        else:
            return redirect('reset_password')

    return render(request, 'reset_password.html')


def actions_after_registration(request, user):
    try:
        Family.objects.get(name='worldwide ranking').members.add(user)
    except Family.DoesNotExist:
        create_internal_error(request, 'Family "worldwide ranking" existiert nicht')
    UserErweitert.objects.create(user=user)


def check_username(request):
    username = request.GET.get('username', None)
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})


def check_email(request):
    email = request.GET.get('email')
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})


@login_required
def get_email_settings(request):
    try:
        user_erweitert = UserErweitert.objects.get(user=request.user)
    except UserErweitert.DoesNotExist:
        create_internal_error(request, f'UserErweitert zu User {request.user} existiert nicht')
    mailinglist = user_erweitert.mailinglist
    return JsonResponse({'mailinglist': mailinglist})
