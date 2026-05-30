import base64
import os
import re

from django.utils import translation


class AddCORSHeaderMiddleware:
    ALLOWED_ORIGINS = {"https://climate-quest.de"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        origin = request.headers.get('Origin')
        if origin in self.ALLOWED_ORIGINS:
            response["Access-Control-Allow-Origin"] = origin
        else:
            if "Access-Control-Allow-Origin" in response:
                del response["Access-Control-Allow-Origin"]

        return response


class GenerateCSPNonceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        script_nonce = base64.b64encode(os.urandom(16)).decode()
        request.csp_script_nonce = script_nonce
        allowed_script_sources = 'https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/ https://storage.googleapis.com/workbox-cdn/releases/5.1.2/'

        style_nonce = base64.b64encode(os.urandom(16)).decode()
        request.csp_style_nonce = style_nonce
        allowed_style_sources = 'https://www.gstatic.com/recaptcha/'

        response = self.get_response(request)

        csp = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{script_nonce}' {allowed_script_sources}; "
            f"style-src 'self' 'nonce-{style_nonce}' {allowed_style_sources}; "
            "img-src 'self' data: blob: https://www.gstatic.com/recaptcha/; "
            "frame-src https://www.google.com/recaptcha/; "
            "connect-src 'self' blob: https://www.google.com/recaptcha/;"
            "media-src blob:;"

            "form-action 'self';"
            "base-uri 'self';"
            "frame-ancestors 'none';"
            "object-src 'none';"
        )
        response["Content-Security-Policy"] = csp

        return response


class LanguageFallbackMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            lang = request.user.usererweitert.lang
            if lang != "de" and lang != "en":
                lang = "en"

            translation.activate(lang)
            request.LANGUAGE_CODE = lang

            return self.get_response(request)

        else:
            accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            lang = self._resolve_language(accept_language)

            translation.activate(lang)
            request.LANGUAGE_CODE = lang

            return self.get_response(request)

    def _resolve_language(self, accept_language):
        entries = []
        for part in accept_language.split(','):
            part = part.strip()
            match = re.match(r'([a-zA-Z]+)(?:-[a-zA-Z0-9]+)?(?:;q=([\d.]+))?', part)
            if match:
                lang_code = match.group(1).lower()
                q = float(match.group(2)) if match.group(2) else 1.0
                entries.append((lang_code, q))

        entries.sort(key=lambda x: x[1], reverse=True)

        for lang_code, _ in entries:
            if lang_code == 'de':
                return 'de'

        return 'en'

class AddGloablVariablesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        request.GLOBAL_VARIABLES = {
            'klimapunkte_for_credit': 500,
        }
        return self.get_response(request)
