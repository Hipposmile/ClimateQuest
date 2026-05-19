from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        # Bereits existierender Google-Account → normaler Login
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email', '').lower()
        User = get_user_model()

        if User.objects.filter(username=email).exists():
            messages.error(
                request,
                "Die E-Mail, die mit deinem Google-Account verknüpft ist, wurde bereits "
                "als Username verwendet. Probiere eine andere Sign Up Methode."
            )
            raise ImmediateHttpResponse(redirect('account_login'))

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.username = data.get('email', '').lower()
        return user

    def sync_google_data(self, request, sociallogin):
        user = sociallogin.user
        extra = sociallogin.account.extra_data

        user.email = extra.get('email', user.email)
        user.username = extra.get('email', user.username).lower()
        user.first_name = extra.get('given_name', user.first_name)
        user.last_name = extra.get('family_name', user.last_name)
        user.save()