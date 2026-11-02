from django.apps import AppConfig


class PersonalsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "personals"

    def ready(self):
        from . import signals  # noqa: F401 - registers the allauth signal receivers
