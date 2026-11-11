from datetime import datetime, timedelta
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from api.gemini_summary import GeminiSummaryUnavailable, summarize_requests
from api.models import Request, Status
from api.pagination import RequestPagination
from api.serializers import (
    LogoutResponseSerializer,
    RequestCreateSerializer,
    RequestSerializer,
    RequestStatusUpdateSerializer,
    RequestSummarySerializer,
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


@extend_schema_view(
    get=extend_schema(
        responses=RequestSerializer(many=True),
        parameters=[
            OpenApiParameter(
                "start_date",
                str,
                OpenApiParameter.QUERY,
                description="Inclusive ISO date/datetime filter.",
            ),
            OpenApiParameter(
                "end_date",
                str,
                OpenApiParameter.QUERY,
                description="Inclusive ISO date/datetime filter.",
            ),
            OpenApiParameter(
                "search",
                str,
                OpenApiParameter.QUERY,
                description="Case-insensitive search in title and description.",
            ),
            OpenApiParameter(
                "q",
                str,
                OpenApiParameter.QUERY,
                description="Alias for search.",
            ),
            OpenApiParameter(
                "status",
                str,
                OpenApiParameter.QUERY,
                description="Filter by status tag.",
            ),
        ],
    ),
    post=extend_schema(
        request=RequestCreateSerializer,
        responses={201: RequestSerializer},
    ),
)
class RequestListCreateView(ListCreateAPIView):
    queryset = Request.objects.select_related("status").all()
    serializer_class = RequestSerializer
    pagination_class = RequestPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method != "GET":
            return queryset

        start_value = self.request.query_params.get("start_date")
        end_value = self.request.query_params.get("end_date")
        today = timezone.localdate()

        if not start_value and not end_value:
            now = timezone.now()
            queryset = queryset.filter(
                created_at__range=(now - timedelta(days=7), now)
            )
        else:
            try:
                end_date = (
                    datetime.fromisoformat(end_value.replace("Z", "+00:00")).date()
                    if end_value
                    else today
                )
                start_date = (
                    datetime.fromisoformat(start_value.replace("Z", "+00:00")).date()
                    if start_value
                    else end_date - timedelta(days=7)
                )
            except ValueError as exc:
                raise ValidationError(
                    {
                        "date": (
                            "Use ISO date or datetime values for start_date and "
                            "end_date."
                        )
                    }
                ) from exc

            if start_date > end_date:
                raise ValidationError(
                    {"date": "start_date must be earlier than or equal to end_date."}
                )

            queryset = queryset.filter(
                created_at__date__range=(start_date, end_date)
            )

        search_term = (
            self.request.query_params.get("search")
            or self.request.query_params.get("q")
            or ""
        ).strip()
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term)
                | Q(description__icontains=search_term)
            )

        status_tag = self.request.query_params.get("status", "").strip()
        if status_tag:
            request_status = Status.objects.filter(tag=status_tag).first()
            queryset = (
                queryset.filter(status=request_status)
                if request_status
                else queryset.none()
            )

        return queryset

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

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RequestCreateSerializer
        return RequestSerializer


@extend_schema(
    responses=RequestSerializer,
)
class RequestStatusUpdateView(GenericAPIView):
    queryset = Request.objects.select_for_update()
    serializer_class = RequestStatusUpdateSerializer

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        response_serializer = RequestSerializer(
            instance,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data)


class RequestSummaryView(GenericAPIView):
    serializer_class = RequestSummarySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        queryset = Request.objects.select_related("status").all()

        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        else:
            one_week_ago = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=one_week_ago)

        recent_requests = list(
            queryset.order_by("-created_at")
            .values("title", "status__tag", "created_at")[:50]
        )

        if not recent_requests:
            summary = "No hay solicitudes recientes en el rango de fechas seleccionado para resumir."
        else:
            try:
                summary = summarize_requests(recent_requests)
            except GeminiSummaryUnavailable:
                return Response(
                    {
                        "success": False,
                        "message": (
                            "El servicio de resumen con IA no está disponible "
                            "en este momento."
                        ),
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        serializer = self.get_serializer(
            {
                "success": True,
                "summary": summary,
                "request_count": len(recent_requests),
            }
        )
        return Response(serializer.data)


class StatusListView(ListAPIView):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
