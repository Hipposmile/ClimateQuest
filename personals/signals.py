from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_updated
from django.dispatch import receiver
from .adapters import MySocialAccountAdapter
from .views import actions_after_registration

@receiver(social_account_updated)
def sync_google_data(sender, request, sociallogin, **kwargs):
    adapter = MySocialAccountAdapter()
    adapter.sync_google_data(request, sociallogin)

@receiver(user_signed_up)
def create_user_profile(sender, request, user, **kwargs):
    actions_after_registration(request, user)