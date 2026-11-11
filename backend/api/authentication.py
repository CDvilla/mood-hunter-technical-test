from rest_framework.authentication import (
    TokenAuthentication,
    get_authorization_header,
)
from rest_framework.exceptions import AuthenticationFailed


class TokenOrBearerAuthentication(TokenAuthentication):
    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth:
            return None

        if auth[0].lower() not in {b"token", b"bearer"}:
            return None

        if len(auth) != 2:
            raise AuthenticationFailed("Invalid token header.")

        try:
            token = auth[1].decode()
        except UnicodeDecodeError as exc:
            raise AuthenticationFailed("Invalid token header.") from exc

        return self.authenticate_credentials(token)

    def authenticate_header(self, request):
        return "Bearer"
