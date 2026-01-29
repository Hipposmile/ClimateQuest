import os
import base64


class AddCORSHeaderMiddleware:
    ALLOWED_ORIGINS = {
        "https://climate-quest.de",
        "https://www.climate-quest.de",
    }

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
        allowed_script_sources = 'https://cdn.jsdelivr.net/npm/quill@2.0.3/dist/quill.js https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/ https://storage.googleapis.com/workbox-cdn/releases/5.1.2/'

        style_nonce = base64.b64encode(os.urandom(16)).decode()
        request.csp_style_nonce = style_nonce
        allowed_style_sources = 'https://cdn.jsdelivr.net/npm/quill@2.0.3/dist/quill.snow.css https://www.gstatic.com/recaptcha/'

        response = self.get_response(request)

        csp = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{script_nonce}' {allowed_script_sources}; "
            f"style-src 'self' 'nonce-{style_nonce}' {allowed_style_sources}; "
            f"img-src 'self' data: https://www.gstatic.com/recaptcha/; "
            f"frame-src https://www.google.com/recaptcha/; "
            f"connect-src 'self' https://www.google.com/recaptcha/;"
        )
        response["Content-Security-Policy"] = csp

        return response
