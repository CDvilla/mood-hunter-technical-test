from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from api.models import Request, Status
from api.serializers import (
    LogoutResponseSerializer,
    RequestCreateSerializer,
    RequestSerializer,
    StatusSerializer,
    TokenLoginSerializer,
    TokenSerializer,
)


def health_check(request):
    return JsonResponse({"status": "ok"})


@extend_schema(responses=TokenSerializer)
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


@extend_schema(request=None)
class TokenLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutResponseSerializer

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "Successfully logged out."})


@extend_schema(responses=RequestSerializer)
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


class StatusListView(ListAPIView):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
