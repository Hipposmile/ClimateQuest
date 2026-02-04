from django.shortcuts import render


def testers(request):
    return render(request, './testers.html')

def aknachhaltigkeit(request):
    return render(request, './aknachhaltigkeit.html')
