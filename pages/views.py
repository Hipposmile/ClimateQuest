from django.shortcuts import render


def testers(request):
    return render(request, './testers.html')
