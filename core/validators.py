from PIL import Image
from django.core.exceptions import ValidationError


def validate_image(file):
    max_size_mb = 5
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Maximal {max_size_mb} MB erlaubt.")

    allowed_extensions = ["jpg", "jpeg", "png", "webp", "avif"]
    ext = file.name.split(".")[-1].lower()

    if ext not in allowed_extensions:
        raise ValidationError("Ungültige Dateiendung.")

    try:
        img = Image.open(file)
        img.verify()
    except Exception:
        raise ValidationError("Die Datei ist kein gültiges Bild.")

    allowed_formats = ["JPEG", "PNG", "WEBP", "AVIF"]

    if img.format not in allowed_formats:
        raise ValidationError("Ungültiger Bildtyp.")

    file.seek(0)
