from utils.functions import createInternerFehler
from django.shortcuts import render


# Create your views here.
def custom_400(request, exception):
    createInternerFehler(request, f'400 Error: {exception}')
    return render(request, '400.html', status=400)

def custom_403(request, exception):
    createInternerFehler(request, f'403 Error: {exception}')
    return render(request, '403.html', status=403)

def csrf_error(request, exception):
    createInternerFehler(request, f'CSRF Error: {exception}')
    return render(request, 'csrf.html', status=500)

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request, exception):
    createInternerFehler(request, f'Interner Serverfehler (500): {exception}')
    return render(request, '500.html', status=500)

def custom_503(request, exception):
    createInternerFehler(request, f'Dienst nicht verfügbar (503): {exception}')
    return render(request, '503.html', status=503)