# templatetags/html_decode.py
import html
from django import template

register = template.Library()

@register.filter
def html_decode(value):
    if isinstance(value, str):
        return html.unescape(value)
    return value