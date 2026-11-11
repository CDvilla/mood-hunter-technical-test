from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token

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


class TokenLoginErrorSerializer(serializers.Serializer):
    non_field_errors = serializers.ListField(
        child=serializers.CharField(),
    )


class AuthenticationErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


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
