from django.conf import settings

def production_only():
    if settings.DEBUG:
        return False
    return True

def development_only():
    if settings.DEBUG:
        return True
    return False