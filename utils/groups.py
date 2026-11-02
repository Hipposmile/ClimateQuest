"""Helpers shared by the family and community views (password-protected groups of users)."""

from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.utils.html import escape

from core.all_messages import all_messages
from utils.functions import create_notification

MAX_FIELD_LENGTH = 100


def notify(request, users, text_de, text_en, url=None):
    """Send the same notification to every user in ``users``; ``url`` may be a callable ``user -> url``."""
    for user in users:
        create_notification(request, text_de, text_en, user, url=url(user) if callable(url) else url)


def escaped(value):
    """HTML-escape a user supplied value before it is placed into a notification."""
    return escape(str(value))


def require_admin_password(request, raw_password, hashed_password, *required_values):
    """Check the form values of a protected action. Flashes the problem and returns False if it must not run."""
    if not raw_password or not all(required_values):
        messages.error(request, all_messages["missing_required_inputs"])
        return False
    if not check_password(raw_password, hashed_password):
        messages.error(request, all_messages["invalid_admin_password"])
        return False
    return True


def too_long(request, *values):
    """True (and flashes the problem) if any submitted value exceeds the model field length."""
    if any(value is not None and len(value) > MAX_FIELD_LENGTH for value in values):
        messages.error(request, all_messages["too_long_input"])
        return True
    return False
