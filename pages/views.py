from django.shortcuts import render


def mobile_apps(request):
    return render(request, './mobile_apps.html')

def aknachhaltigkeit(request):
    return render(request, './aknachhaltigkeit.html')
