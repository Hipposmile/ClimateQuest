from functools import wraps

from django.conf import settings
from django.shortcuts import render


def development_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not settings.DEBUG:
            return render(request, "development_only.html")
        return view_func(request, *args, **kwargs)

    return wrapper

def production_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if settings.DEBUG:
            return render(request, "production_only.html")
        return view_func(request, *args, **kwargs)

    return wrapper
