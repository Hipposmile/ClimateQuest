from django.conf import settings
from django.utils.functional import SimpleLazyObject


def vapid_key(request):
    return {"vapid_public_key": settings.WEBPUSH_SETTINGS.get("VAPID_PUBLIC_KEY")}


def _count_notifications(user):
    from home.models import Benachrichtigung

    return Benachrichtigung.objects.filter(user=user).count()


def notification_count(request):
    """Number of notifications of the logged-in user.

    Lazy: the COUNT query only runs when a template really renders the value, and it replaces the extra
    HTTP request (with session lookup, middleware and JSON response) that every page used to send.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    return {"benachrichtigungen_count": SimpleLazyObject(lambda: _count_notifications(user))}
