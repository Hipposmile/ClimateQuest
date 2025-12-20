from utils.functions import createInternerFehler

# Create your views here.
def custom_400(request, exception):
    return render(request, '400.html', status=400)

def custom_403(request, exception):
    return render(request, '403.html', status=403)

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    # Interne Fehlerbehandlung
    createInternerFehler(request, 'Interner Serverfehler (500)')
    return render(request, '500.html', status=500)

def custom_503(request, exception=None):
    createInternerFehler(request, 'Dienst nicht verfügbar (503)')
    return render(request, '503.html', status=503)

# Notifications
from django.http.response import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from webpush import send_user_notification
import json
from django.conf import settings

@require_GET
def home(request):
   webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
   vapid_key = webpush_settings.get('VAPID_PUBLIC_KEY')
   user = request.user
   return render(request, './test.html', {user: user, 'vapid_key': vapid_key})

def send_push(benachrichtigung, user, head="Neue Benachrichtigung"):
    try:
        payload = {'head': head, 'body': benachrichtigung}
        send_user_notification(user=user, payload=payload, ttl=1000)

        return JsonResponse(status=200, data={"message": "Web push successful"})
    except TypeError:
        return JsonResponse(status=500, data={"message": "An error occurred"})