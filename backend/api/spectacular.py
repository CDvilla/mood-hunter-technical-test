from drf_spectacular.extensions import OpenApiAuthenticationExtension


class TokenAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "api.authentication.TokenOrBearerAuthentication"
    name = "tokenAuth"
    priority = 1

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": (
                "Enter the token value only. Swagger UI adds the required "
                "`Bearer ` prefix to the Authorization header."
            ),
        }
