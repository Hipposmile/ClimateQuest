"""Settings for the test suite.

The database is chosen with ``TEST_DB=sqlite`` (default) or ``TEST_DB=postgres``.
For PostgreSQL the usual ``PGHOST``, ``PGPORT``, ``PGUSER``, ``PGPASSWORD`` and
``PGDATABASE`` variables are honoured.
"""

import os

from .base_settings import *  # noqa: F403

SECRET_KEY = "test-only-secret-key-not-used-anywhere-else-0123456789"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

if os.environ.get("TEST_DB", "sqlite") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("PGDATABASE", "climatequest"),
            "USER": os.environ.get("PGUSER", "postgres"),
            "PASSWORD": os.environ.get("PGPASSWORD", ""),
            "HOST": os.environ.get("PGHOST", "localhost"),
            "PORT": os.environ.get("PGPORT", "5432"),
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
