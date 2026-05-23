import uuid

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect

from core.all_messages import all_messages


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def _extract_email(self, sociallogin):
        email = sociallogin.account.extra_data.get("email")
        return email if email else ""

    def _extract_name(self, sociallogin):
        data = sociallogin.account.extra_data

        # Apple: "name" kommt nur beim ersten Login
        if "name" in data and isinstance(data["name"], dict):
            full_name = f"{data['name'].get('firstName', '')} {data['name'].get('lastName', '')}".strip()
            if full_name:
                return full_name

        # Google
        given = data.get("given_name")
        family = data.get("family_name")
        if given or family:
            return f"{given or ''} {family or ''}".strip()

        # GitHub & andere
        if data.get("name"):
            return data["name"]

        return None

    def _generate_uuid_username(self):
        return f"user-{uuid.uuid4().hex[:12]}"

    def _build_username(self, sociallogin):
        name = self._extract_name(sociallogin)
        if name and not User.objects.filter(username=name).exists():
            return name

        email = self._extract_email(sociallogin)
        if email and not User.objects.filter(email=email).exists():
            return email

        return self._generate_uuid_username()

    def pre_social_login(self, request, sociallogin):
        username = self._build_username(sociallogin)
        if User.objects.filter(username=username).exists():
            messages.error(request, all_messages["username_not_available"])
            raise ImmediateHttpResponse(
                HttpResponseRedirect("/personals/login/")
            )

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.username = self._build_username(sociallogin)
        email = self._extract_email(sociallogin)
        user.email = email if not User.objects.filter(email=email).exists() else ""
        return user
