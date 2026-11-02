from django.contrib.auth.hashers import identify_hasher, make_password


def _is_hashed(value):
    try:
        identify_hasher(value)
    except ValueError:
        return False
    return True


class HashPasswordsOnSaveMixin:
    """Model mixin: ``password`` and ``admin_password`` are hashed on save unless they already are hashes."""

    def save(self, *args, **kwargs):
        for field in ("password", "admin_password"):
            value = getattr(self, field)
            if not _is_hashed(value):
                setattr(self, field, make_password(value))
        super().save(*args, **kwargs)
