from django import template
from utils.functions import get_family_rank_from_user

register = template.Library()

@register.filter
def get_family_rank(user, family):
    return get_family_rank_from_user(user, family)