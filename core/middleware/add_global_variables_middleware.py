class AddGloablVariablesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.GLOBAL_VARIABLES = {
            'klimapunkte_for_credit': 500,
        }
        return self.get_response(request)
