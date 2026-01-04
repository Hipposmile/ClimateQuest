from django.shortcuts import render
from utils.functions import *
from datetime import timedelta
from django.test import RequestFactory


# Create your views here.
def custom_400(request, exception=""):
    create_internal_error(request, f'400 Error: {exception}')
    return render(request, '400.html', status=400)


def custom_403(request, exception=""):
    create_internal_error(request, f'403 Error: {exception}')
    return render(request, '403.html', status=403)


def csrf_error(request, reason=""):
    create_internal_error(request, f'CSRF Error: {reason}')
    return render(request, 'csrf.html', status=500)


def custom_404(request, exception=""):
    return render(request, '404.html', status=404)


def custom_500(request, exception=""):
    create_internal_error(request, f'Interner Serverfehler (500): {exception}', '', None, False)
    return render(request, '500.html', status=500)


def custom_503(request, exception=""):
    create_internal_error(request, f'Dienst nicht verfügbar (503): {exception}')
    return render(request, '503.html', status=503)


factory = RequestFactory()
fake_request = factory.get('/')


def create_reminder():
    for user in User.objects.all():
        try:
            if not Aktion.objects.filter(user=user, date__gte=timezone.now().date() - timedelta(days=7)).exists():
                fake_request = fake_request.user = user
                create_notification(fake_request,
                                    notification=f"Hey {user.username}, du hast in der letzten Woche keine einzige Aktion eingetragen! Ändere das und schütze nicht nur das Klima, sondern steige auch in den Rankings deiner Families und Communities sowie in deinem Level auf!",
                                    user=user)
        except Exception as e:
            error_message = f'Cronjob: {timezone.now().isoformat()} Create Reminder for User: {user}: Exception: {e}'
            create_internal_error(fake_request, error_message)
