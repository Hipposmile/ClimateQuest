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
