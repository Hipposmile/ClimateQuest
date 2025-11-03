from django import template

register = template.Library()

@register.filter
def html_range(value):
    try:
        return range(int(value))
    except:
        return []