from django.shortcuts import render
from utils.functions import *

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