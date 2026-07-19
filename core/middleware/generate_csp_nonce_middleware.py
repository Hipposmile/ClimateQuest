import base64
import os


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
