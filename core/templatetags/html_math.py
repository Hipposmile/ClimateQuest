from django import template

register = template.Library()


@register.filter
def percent(value, arg):
    """``value`` as percentage of ``arg`` (0 for invalid input or division by zero)."""
    try:
        return float(value) / float(arg) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
