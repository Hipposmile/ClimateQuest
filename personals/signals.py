from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from .views import actions_after_registration


@receiver(user_signed_up)
def create_user_profile(sender, request, user, **kwargs):
    actions_after_registration(request, user)
