from django.contrib import messages
from django.shortcuts import render, redirect

from core.all_messages import all_messages
from .models import *


# Create your views here.
def presents_overview(request):
    own_presents = Present.objects.filter(creator=request.user)
    return render(request, './presents_overview.html', {'own_presents': own_presents})

def add_present(request):
    if request.method == 'POST':
        recipient = request.POST.get('recipient_name')
        if len(recipient) > 100:
            messages.error(request, all_messages["input_too_long"])
            return redirect('add_present')
        present = Present.objects.create(
            recipient=recipient,
            creator=request.user
        )
        messages.success(request, all_messages["present_created"])
        return redirect('present_detail', present_secret_key=present.secret_key)
    return render(request, './add_present.html')

def present_detail(request, present_secret_key):
    try:
        present = Present.objects.get(secret_key=present_secret_key)
    except Present.DoesNotExist:
        messages.error(request, all_messages["present_not_found"])
        return redirect('presents_overview')
    
    if request.method == 'POST':
        if 'add_congratulation' in request.POST:
            message = request.POST.get('msg')
            congratulator = request.POST.get('congratulator')
            if len(congratulator) > 100:
                messages.error(request, all_messages["input_too_long"])
                return redirect('present_detail', present.secret_key)
            congratulation = Congratulation.objects.create(
                message=message,
                congratulator=congratulator
            )
            present.congratulations.add(congratulation)
            messages.success(request, all_messages["congratulation_added"])
            return redirect('present_detail', present_secret_key=present.secret_key)
        elif 'light_candle' in request.POST:
            present.candles += 1
            present.save()
            return redirect('present_detail', present_secret_key=present.secret_key)
    return render(request, './present_detail.html', {'present': present})

def delete_present(request, present_secret_key):
    try:
        present = Present.objects.get(secret_key=present_secret_key, creator=request.user)
    except Present.DoesNotExist:
        messages.error(request, all_messages["present_not_found"])
        return redirect('presents_overview')

    for congratulation in present.congratulations.all():
        congratulation.delete()
    present.delete()
    messages.success(request, all_messages["present_deleted"])
    return redirect('presents_overview')