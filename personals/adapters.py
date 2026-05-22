import uuid

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def _extract_email(self, sociallogin):
        email = sociallogin.account.extra_data.get("email")
        return email.lower() if email else None

    def _extract_name(self, sociallogin):
        data = sociallogin.account.extra_data

        # Apple: "name" kommt nur beim ersten Login
        if "name" in data and isinstance(data["name"], dict):
            full_name = f"{data['name'].get('firstName', '')} {data['name'].get('lastName', '')}".strip()
            if full_name:
                return full_name.lower()

        # Google
        given = data.get("given_name")
        family = data.get("family_name")
        if given or family:
            return f"{given or ''} {family or ''}".strip().lower()

        # GitHub & andere
        if data.get("name"):
            return data["name"].lower()

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
        return

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.username = self._build_username(sociallogin)
        email = self._extract_email(sociallogin)
        user.email = email if not User.objects.filter(email=email).exists() else None
        return user
