from django.http import JsonResponse
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from api.models import Request, Status
from api.serializers import (
    AuthenticationErrorSerializer,
    LogoutResponseSerializer,
    RequestCreateSerializer,
    RequestSerializer,
    RequestValidationErrorSerializer,
    StatusSerializer,
    TokenLoginErrorSerializer,
    TokenLoginSerializer,
    TokenSerializer,
)


def health_check(request):
    return JsonResponse({"status": "ok"})


@extend_schema(
    summary="Log in",
    description=(
        "Validates a username and password and returns the user's DRF token. "
        "Invalid credentials return the same generic error. Use the token in "
        "subsequent protected requests as `Authorization: Token <token>`."
    ),
    responses={
        200: TokenSerializer,
        400: OpenApiResponse(
            response=TokenLoginErrorSerializer,
            description="Invalid credentials; the response does not reveal which field was incorrect.",
        ),
    },
    examples=[
        OpenApiExample(
            "Login",
            value={
                "username": "admin",
                "password": "replace-with-your-password",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Token",
            value={"token": "0123456789abcdef0123456789abcdef01234567"},
            response_only=True,
            status_codes=["200"],
        ),
        OpenApiExample(
            "Invalid credentials",
            value={"non_field_errors": ["Invalid username or password."]},
            response_only=True,
            status_codes=["400"],
        ),
    ],
)
class TokenLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = TokenLoginSerializer

    def post(self, request):
        serializer = TokenLoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


@extend_schema(
    summary="Log out",
    description="Deletes the authenticated user's current DRF token.",
    request=None,
    responses={
        200: LogoutResponseSerializer,
        401: OpenApiResponse(
            response=AuthenticationErrorSerializer,
            description="Authentication credentials were not provided or are invalid.",
        ),
    },
    examples=[
        OpenApiExample(
            "Logged out",
            value={"detail": "Successfully logged out."},
            response_only=True,
            status_codes=["200"],
        ),
        OpenApiExample(
            "Missing or invalid token",
            value={"detail": "Invalid token."},
            response_only=True,
            status_codes=["401"],
        ),
    ],
)
class TokenLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutResponseSerializer

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "Successfully logged out."})


@extend_schema(
    summary="Create a request",
    description=(
        "Creates a request using its title and description. The backend always "
        "sets its initial status to `created`. The response exposes the stable "
        "status tag, never the catalog's numeric ID."
    ),
    responses={
        201: RequestSerializer,
        400: OpenApiResponse(
            response=RequestValidationErrorSerializer,
            description="The request payload is invalid.",
        ),
        401: OpenApiResponse(
            response=AuthenticationErrorSerializer,
            description="Authentication credentials were not provided or are invalid.",
        ),
    },
    examples=[
        OpenApiExample(
            "Create request",
            value={
                "title": "Review application",
                "description": "Review the submitted application.",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Created request",
            value={
                "id": 1,
                "title": "Review application",
                "description": "Review the submitted application.",
                "status": "created",
                "created_at": "2026-11-10T12:00:00Z",
                "updated_at": "2026-11-10T12:00:00Z",
            },
            response_only=True,
            status_codes=["201"],
        ),
        OpenApiExample(
            "Invalid request",
            value={"title": ["This field is required."]},
            response_only=True,
            status_codes=["400"],
        ),
    ],
)
class RequestCreateView(CreateAPIView):
    queryset = Request.objects.all()
    serializer_class = RequestCreateSerializer

    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        instance = input_serializer.save()
        output_serializer = RequestSerializer(
            instance,
            context=self.get_serializer_context(),
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


@extend_schema(
    summary="List request statuses",
    description=(
        "Returns the available statuses in deterministic order. Statuses are "
        "managed by database migrations and cannot be changed through this API."
    ),
    responses={
        200: StatusSerializer(many=True),
        401: OpenApiResponse(
            response=AuthenticationErrorSerializer,
            description="Authentication credentials were not provided or are invalid.",
        ),
    },
)
class StatusListView(ListAPIView):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
