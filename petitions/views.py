from PIL import Image
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render

from core.all_messages import all_messages
from core.views import production
from petitions.models import *
from utils.functions import clean_html, clean_img

# Create your views here.
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "avif"]
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/avif", ]
MAX_SIZE_MB = 5


@production
@login_required
def add_petition(request):
    categories = Category.objects.all().order_by('title')
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        img = request.FILES.get('img')
        category_input = request.POST.get('category')

        if not title or not content or not img:
            messages.error(request, all_messages["missing_required_inputs"])

        try:
            category = Category.objects.get(title=category_input)
        except Category.DoesNotExist:
            messages.error(request, all_messages["internal_error"])
            return redirect("add_petition")

        content = clean_html(content)

        valid, response = clean_img(img)
        if not valid:
            messages.error(request, response)
            return redirect("add_petition")
        img = response
        width, height = Image.open(img).size
        print(width, height)
        if width / height != 16 / 9:
            messages.error(request, all_messages["invalid_img_proportions"])
            return redirect("add_petition")

        petition = Petition.objects.create(title=title, content=content, img=img, category=category)
        messages.success(request, all_messages["petition_added"])
        return redirect("petition_detail", petition.id)

    return render(request, "./add_petition.html", {'categories': categories})


@production
def petition_detail(request, petition_id): # ToDo: Add comments
    try:
        petition = Petition.objects.get(id=petition_id)
    except Petition.DoesNotExist:
        messages.error(request, all_messages["petition_not_found"])
        return redirect("petitions_overview")

    if request.method == 'POST':
        if request.user.is_authenticated:
            if request.user not in petition.signs.all():
                petition.signs.add(request.user)
                petition.save()
                messages.success(request, all_messages["petition_signed"])
            else:
                petition.signs.remove(request.user)
                petition.save()
                messages.success(request, all_messages["petition_unsigned"])

    return render(request, "./petition_detail.html", {"petition": petition})

# ToDo: Add update functionality

@production
def petitions_overview(request): # ToDo: Add functionality, e.g. like artikel_overview, but using categories
    return render(request, "./petitions_overview.html")
