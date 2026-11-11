from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from api.domain import (
    InvalidRequestStatusTransition,
    validate_request_status_transition,
)
from api.models import Request, Status


class RequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ["title", "description"]

    def create(self, validated_data):
        created_status = Status.objects.get(tag="created")
        return Request.objects.create(status=created_status, **validated_data)


class RequestSerializer(serializers.ModelSerializer):
    status = serializers.SlugRelatedField(
        read_only=True,
        slug_field="tag",
    )

    class Meta:
        model = Request
        fields = ["id", "title", "description", "status", "created_at", "updated_at"]
        read_only_fields = fields


class RequestStatusUpdateSerializer(serializers.Serializer):
    status = serializers.SlugRelatedField(
        queryset=Status.objects.all(),
        slug_field="tag",
    )

    def validate(self, attrs):
        extra_fields = set(self.initial_data) - {"status"}
        if extra_fields:
            raise serializers.ValidationError(
                {
                    field: ["Only the status field may be updated."]
                    for field in sorted(extra_fields)
                }
            )

        try:
            validate_request_status_transition(
                self.instance.status.tag,
                attrs["status"].tag,
            )
        except InvalidRequestStatusTransition as exc:
            raise serializers.ValidationError({"status": str(exc)}) from exc

        return attrs

    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.save(update_fields=["status", "updated_at"])
        return instance


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ["tag", "name"]
        read_only_fields = fields


class TokenLoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        token, _ = Token.objects.get_or_create(user=user)
        return {"token": token.key}


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class LogoutResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
