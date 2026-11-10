import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Ensure that the configured native Django administrator exists."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not username or not password:
            raise CommandError(
                "DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD "
                "must both be configured."
            )

        User = get_user_model()
        user = User._default_manager.filter(username=username).first()
        if user is not None:
            if not user.is_superuser:
                raise CommandError(
                    f"The configured administrator username '{username}' "
                    "already belongs to a non-superuser account."
                )
            if not user.is_staff:
                user.is_staff = True
                user.save(update_fields=["is_staff"])
            self.stdout.write(f"Administrator '{username}' already exists.")
            return

        candidate = User(username=username)
        try:
            validate_password(password, user=candidate)
        except ValidationError as error:
            raise CommandError(
                f"The configured administrator password is invalid: {error}"
            ) from error

        User._default_manager.create_superuser(
            username=username,
            email="",
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Created administrator '{username}'.")
        )
