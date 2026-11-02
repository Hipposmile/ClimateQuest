from functools import lru_cache

import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = ["a", "b", "strong", "i", "em", "u", "br", "p", "ul", "ol", "li", "h1", "h2", "span"]
ALLOWED_CLASS = "emoji"


def _allow_attribute(tag, name, value):
    if tag == "a":
        return name in {"href", "target", "rel"}
    return tag == "span" and name == "class" and value == ALLOWED_CLASS


@lru_cache(maxsize=4096)
def _sanitize(text):
    return mark_safe(bleach.clean(text, tags=ALLOWED_TAGS, attributes=_allow_attribute, strip=False))  # noqa: S308


@register.filter(is_safe=True)
def safe_html(value):
    """Render HTML written by the application (flash messages, notifications) or by users.

    Replaces ``|safe``: markup that is not on the allow-list is shown as text, so values such as user names
    or chat messages that were interpolated into a message cannot inject scripts.
    """
    return _sanitize(str(value)) if value else ""
