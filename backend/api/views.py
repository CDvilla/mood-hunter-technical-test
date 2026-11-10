from django.http import JsonResponse
from rest_framework.viewsets import ModelViewSet

from api.models import Item
from api.serializers import ItemSerializer


def health_check(request):
    return JsonResponse({"status": "ok"})


class ItemViewSet(ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
