from django.conf import settings
from django.http import HttpResponse
from django.utils.cache import patch_vary_headers


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin")
        allowed = origin in settings.CORS_ALLOWED_ORIGINS

        if request.method == "OPTIONS" and allowed:
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        if allowed:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
            response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response["Access-Control-Max-Age"] = "86400"
            patch_vary_headers(response, ["Origin"])

        return response
