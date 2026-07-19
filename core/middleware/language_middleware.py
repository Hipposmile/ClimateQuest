from __future__ import annotations

import logging
import re
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.utils import translation

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGE_CODES: tuple[str, ...] = ("de", "en")
DEFAULT_LANGUAGE_CODE: str = "en"
LANGUAGE_PREFIX_PATTERN = re.compile(r"^/(de|en)(/.*|$)")
EXCLUDED_PATH_PREFIXES: tuple[str, ...] = tuple(
    prefix for prefix in (settings.STATIC_URL, settings.MEDIA_URL) if prefix
)


class LanguageFallbackMiddleware:
    """Erzwingt ein /de/ oder /en/ URL-Prefix und aktiviert die passende Sprache."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if is_excluded_path(request.path_info):
            return self.get_response(request)

        language_code = get_language_code_from_path(request.path_info)
        if language_code is None:
            target_language_code = resolve_target_language_code(request)
            return build_redirect_with_language_prefix(request, target_language_code)

        request.path_info = strip_language_prefix(request.path_info, language_code)
        translation.activate(language_code)
        request.LANGUAGE_CODE = language_code

        return self.get_response(request)


def is_excluded_path(path_info: str) -> bool:
    """Statische Dateien und Medien sollen kein Sprach-Prefix erhalten."""
    return any(path_info.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES)


def get_language_code_from_path(path_info: str) -> Optional[str]:
    match = LANGUAGE_PREFIX_PATTERN.match(path_info)
    if match is None:
        return None
    return match.group(1)


def strip_language_prefix(path_info: str, language_code: str) -> str:
    stripped_path = path_info[len(language_code) + 1:]
    return stripped_path or "/"


def build_redirect_with_language_prefix(
        request: HttpRequest, language_code: str
) -> HttpResponseRedirect:
    query_string = request.META.get("QUERY_STRING", "")
    query_suffix = f"?{query_string}" if query_string else ""
    return HttpResponseRedirect(f"/{language_code}{request.path_info}{query_suffix}")


def resolve_target_language_code(request: HttpRequest) -> str:
    if request.user.is_authenticated:
        return resolve_user_language_code(request.user)
    return resolve_browser_language_code(request.META.get("HTTP_ACCEPT_LANGUAGE", ""))


def resolve_user_language_code(user: "AbstractBaseUser | AnonymousUser") -> str:
    try:
        language_code = user.usererweitert.lang
    except (ObjectDoesNotExist, AttributeError):
        logger.exception(
            "Sprachpräferenz für User %s konnte nicht gelesen werden.", user.pk
        )
        return DEFAULT_LANGUAGE_CODE
    if language_code not in SUPPORTED_LANGUAGE_CODES:
        return DEFAULT_LANGUAGE_CODE
    return language_code


def resolve_browser_language_code(accept_language_header: str) -> str:
    for language_code, _ in parse_accept_language_header(accept_language_header):
        if language_code == "de":
            return "de"
    return DEFAULT_LANGUAGE_CODE


def parse_accept_language_header(accept_language_header: str) -> list[tuple[str, float]]:
    entries = [
        entry
        for part in accept_language_header.split(",")
        if (entry := parse_accept_language_entry(part.strip())) is not None
    ]
    entries.sort(key=lambda entry: entry[1], reverse=True)
    return entries


def parse_accept_language_entry(part: str) -> Optional[tuple[str, float]]:
    match = re.match(r"([a-zA-Z]+)(?:-[a-zA-Z0-9]+)?(?:;q=([\d.]+))?", part)
    if match is None:
        return None
    language_code = match.group(1).lower()
    quality = float(match.group(2)) if match.group(2) else 1.0
    return language_code, quality
