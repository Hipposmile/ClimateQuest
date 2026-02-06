from django.shortcuts import render

from core.all_messages import all_messages
from petitions.models import *

# Create your views here.
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "avif"]
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/avif", ]
MAX_SIZE_MB = 5


def add_petition(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        img = request.FILES.get('img')

        if not title or not content or not img:
            messages.error(request, all_messages["missing_required_inputs"])

        if img.size > MAX_SIZE_MB * 1024 * 1024:
            messages.error(request, all_messages["size_exceeded_maximum"].format(max_size_mb=MAX_SIZE_MB))
            return redirect("add_petition")

        ext = img.name.split(".")[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            messages.error(request, all_messages["invalid_file_extension"])
            return redirect("add_petition")

        try:
            image = Image.open(img)
            image.verify()
        except Exception:
            messages.error(request, all_messages["invalid_img"])
            return redirect("add_petition")

        if image.format not in ALLOWED_FORMATS:
            messages.error(request, all_messages["invalid_file_type"])
            return redirect("add_petition")

        img.seek(0)

        petition = Petition.objects.create(title=title, content=content, img=img)
        messages.success(request, all_messages["petition_added"])
        return redirect("home")

    return render(request, "./add_petition.html")


from PIL import Image
from django.contrib import messages
from django.shortcuts import redirect

MAX_SIZE_MB = 5
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "avif"]
ALLOWED_FORMATS = ["JPEG", "PNG", "WEBP", "AVIF"]


def upload_image_view(request):
    if request.method == "POST":
        img = request.FILES.get("image")

        if not img:
            messages.error(request, "Bitte eine Datei auswählen.")
            return redirect("upload")

        # 1. Dateigröße prüfen

        # Wenn alles ok → speichern
        profile = request.user.profile
        profile.avatar = img
        profile.save()

        messages.success(request, "Bild erfolgreich hochgeladen.")
        return redirect("profile")

    return redirect("upload")
