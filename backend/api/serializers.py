from rest_framework import serializers

from api.models import Item, Request


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ["title", "description"]


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ["id", "title", "description", "status", "created_at", "updated_at"]
        read_only_fields = fields


class RequestValidationErrorSerializer(serializers.Serializer):
    title = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    description = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    non_field_errors = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
