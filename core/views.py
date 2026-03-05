from django.contrib.auth.models import User
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from utils.functions import create_internal_error, get_weekly_goal_from_user, create_notification


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
    return render(request, '5xx.html', status=500)


def custom_503(request, exception=""):
    create_internal_error(request, f'Dienst nicht verfügbar (503): {exception}')
    return render(request, '5xx.html', status=503)


from django.conf import settings
from django.shortcuts import render
from functools import wraps


def development_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not settings.DEBUG:
            return render(request, "development_only.html")
        return view_func(request, *args, **kwargs)

    return wrapper


factory = RequestFactory()
fake_request = factory.get('/')


def create_reminder():
    for user in User.objects.all():
        try:
            if get_weekly_goal_from_user(user)[-1] < 100:
                fake_request = fake_request.user = user
                create_notification(fake_request,
                                    notification=f"Hey {user.username}, du hast dein wöchentliches Ziel noch nicht erreicht! Trage jetzt noch eine Aktion ein, die du durchgeführt hast, und erreiche nicht nur dein Ziel, sondern verlängere auch deine Streak!",
                                    user=user,
                                    url=reverse('dashboard'))
        except Exception as e:
            error_message = f'Cronjob: {timezone.now().isoformat()} Create Reminder for User: {user}: Exception: {e}'
            create_internal_error(fake_request, error_message)


def get_default_user():
    return User.objects.filter(is_superuser=True).first().id
