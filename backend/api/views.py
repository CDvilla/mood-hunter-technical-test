from django.http import JsonResponse
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.models import Item, Request
from api.serializers import (
    ItemSerializer,
    RequestCreateSerializer,
    RequestSerializer,
    RequestValidationErrorSerializer,
)


def health_check(request):
    return JsonResponse({"status": "ok"})


class ItemViewSet(ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


@extend_schema(
    summary="Create a request",
    description=(
        "Creates a request using its title and description. The backend always "
        "sets its initial status to `created`; status codes are stable text "
        "values rather than database catalog IDs."
    ),
    request=RequestCreateSerializer,
    responses={
        201: RequestSerializer,
        400: OpenApiResponse(
            response=RequestValidationErrorSerializer,
            description="The request payload is invalid.",
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
