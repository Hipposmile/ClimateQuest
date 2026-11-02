"""Development settings. Production uses ``ClimateQuest.settingsprod``."""

import os

from .base_settings import *  # noqa: F403
from .base_settings import BASE_DIR

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-development-only-key")

DEBUG = True

ALLOWED_HOSTS = ["localhost", "192.168.178.120", "127.0.0.1", "10.0.2.2"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

INTERNAL_IPS = [
    "127.0.0.1",
]

INSTALLED_APPS = [*INSTALLED_APPS, "django_browser_reload"]  # noqa: F405
MIDDLEWARE = [*MIDDLEWARE, "django_browser_reload.middleware.BrowserReloadMiddleware"]  # noqa: F405
