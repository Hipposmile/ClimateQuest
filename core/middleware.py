class AddCORSHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Header setzen, z.B. für alle Domains:
        response["Access-Control-Allow-Origin"] = "https://climate-quest.de", "https://www.climate-quest.de"
        return response
