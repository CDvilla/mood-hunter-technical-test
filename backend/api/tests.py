import json
import os
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from api.domain import (
    ALLOWED_STATUS_TRANSITIONS,
    InvalidRequestStatusTransition,
    validate_request_status_transition,
)
from api.models import Request, Status
from api.serializers import RequestSerializer


class AuthenticatedAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            username="authenticated-test-user",
            password="test-password",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )


class AuthenticationApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="login-test-user",
            password="Valid-Test-Password-58!",
        )

    def test_login_returns_the_users_token(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "login-test-user",
                "password": "Valid-Test-Password-58!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {"token": Token.objects.get(user=self.user).key},
        )

    def test_invalid_credentials_return_a_generic_error(self):
        invalid_password = self.client.post(
            "/api/auth/login/",
            {"username": "login-test-user", "password": "wrong-password"},
            format="json",
        )
        unknown_user = self.client.post(
            "/api/auth/login/",
            {"username": "unknown-user", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(invalid_password.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(unknown_user.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid_password.data, unknown_user.data)
        self.assertEqual(
            invalid_password.data["non_field_errors"][0],
            "Invalid username or password.",
        )

    def test_business_endpoints_reject_missing_and_invalid_tokens(self):
        for authorization in (
            None,
            "Token invalid-token",
            "Bearer invalid-token",
        ):
            headers = {}
            if authorization:
                headers["HTTP_AUTHORIZATION"] = authorization

            with self.subTest(authorization=authorization):
                statuses_response = self.client.get(
                    "/api/statuses/",
                    **headers,
                )
                requests_response = self.client.post(
                    "/api/requests/",
                    {"title": "Protected", "description": "Needs a token"},
                    format="json",
                    **headers,
                )
                update_response = self.client.patch(
                    "/api/requests/1/",
                    {"status": "in_review"},
                    format="json",
                    **headers,
                )
                self.assertEqual(
                    statuses_response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )
                self.assertEqual(
                    requests_response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )
                self.assertEqual(
                    update_response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

    def test_bearer_authentication_accepts_existing_drf_tokens(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token.key}",
        )

        response = self.client.get("/api/statuses/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_deletes_token_and_invalidates_access(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

        logout_response = self.client.post("/api/auth/logout/")

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            logout_response.data,
            {"detail": "Successfully logged out."},
        )
        self.assertFalse(Token.objects.filter(key=token.key).exists())
        self.assertEqual(
            self.client.get("/api/statuses/").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_schema_documents_token_authentication_and_auth_endpoints(self):
        response = self.client.get("/api/schema/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema = response.data
        self.assertIn("tokenAuth", schema["components"]["securitySchemes"])
        self.assertEqual(
            schema["components"]["securitySchemes"]["tokenAuth"],
            {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": (
                    "Enter the token value only. Swagger UI adds the required "
                    "`Bearer ` prefix to the Authorization header."
                ),
            },
        )
        self.assertNotIn("TokenLoginError", schema["components"]["schemas"])
        self.assertNotIn("AuthenticationError", schema["components"]["schemas"])
        self.assertNotIn("RequestValidationError", schema["components"]["schemas"])
        self.assertNotIn("/api/schema/", schema["paths"])
        self.assertIn("/api/auth/login/", schema["paths"])
        self.assertIn("/api/auth/logout/", schema["paths"])
        login = schema["paths"]["/api/auth/login/"]["post"]
        logout = schema["paths"]["/api/auth/logout/"]["post"]
        request_create = schema["paths"]["/api/requests/"]["post"]
        request_list = schema["paths"]["/api/requests/"]["get"]
        request_status_update = schema["paths"]["/api/requests/{id}/"]["patch"]
        statuses = schema["paths"]["/api/statuses/"]["get"]
        self.assertEqual(
            login["requestBody"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/TokenLogin",
        )
        self.assertEqual(
            login["responses"]["200"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/Token",
        )
        self.assertNotIn("requestBody", logout)
        self.assertEqual(
            logout["responses"]["200"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/LogoutResponse",
        )
        self.assertEqual(
            request_create["requestBody"]["content"]["application/json"]["schema"][
                "$ref"
            ],
            "#/components/schemas/RequestCreate",
        )
        self.assertEqual(
            request_create["responses"]["201"]["content"]["application/json"][
                "schema"
            ]["$ref"],
            "#/components/schemas/Request",
        )
        self.assertEqual(
            request_list["responses"]["200"]["content"]["application/json"][
                "schema"
            ],
            {
                "type": "array",
                "items": {"$ref": "#/components/schemas/Request"},
            },
        )
        self.assertEqual(
            request_status_update["requestBody"]["content"]["application/json"][
                "schema"
            ]["$ref"],
            "#/components/schemas/PatchedRequestStatusUpdate",
        )
        self.assertEqual(
            set(
                schema["components"]["schemas"]["PatchedRequestStatusUpdate"][
                    "properties"
                ]
            ),
            {"status"},
        )
        self.assertEqual(
            request_status_update["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["$ref"],
            "#/components/schemas/Request",
        )
        self.assertEqual(
            statuses["responses"]["200"]["content"]["application/json"]["schema"],
            {
                "type": "array",
                "items": {"$ref": "#/components/schemas/Status"},
            },
        )
        self.assertEqual(set(login["responses"]), {"200"})
        self.assertEqual(set(logout["responses"]), {"200"})
        self.assertEqual(set(request_create["responses"]), {"201"})
        self.assertEqual(set(request_list["responses"]), {"200"})
        self.assertEqual(set(statuses["responses"]), {"200"})
        for path, path_item in schema["paths"].items():
            for method, operation in path_item.items():
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue

                with self.subTest(path=path, method=method):
                    if (path, method) in {
                        ("/api/auth/login/", "post"),
                    }:
                        self.assertFalse(any(operation.get("security", [])))
                    else:
                        self.assertEqual(
                            operation.get("security"),
                            [{"tokenAuth": []}],
                        )


class EnsureAdminUserCommandTests(TestCase):
    def test_admin_creation_is_idempotent_and_password_is_configured(self):
        password = "Strong-Admin-Passphrase-981!"
        environment = {
            "DJANGO_SUPERUSER_USERNAME": "automatic-admin-test",
            "DJANGO_SUPERUSER_PASSWORD": password,
        }

        with patch.dict(os.environ, environment):
            call_command("ensure_admin_user", stdout=StringIO())
            call_command("ensure_admin_user", stdout=StringIO())

        User = get_user_model()
        self.assertEqual(
            User.objects.filter(
                username=environment["DJANGO_SUPERUSER_USERNAME"]
            ).count(),
            1,
        )
        user = User.objects.get(username=environment["DJANGO_SUPERUSER_USERNAME"])
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password(password))

    def test_admin_creation_requires_environment_credentials(self):
        with patch.dict(
            os.environ,
            {
                "DJANGO_SUPERUSER_USERNAME": "",
                "DJANGO_SUPERUSER_PASSWORD": "",
            },
        ):
            with self.assertRaises(CommandError):
                call_command("ensure_admin_user", stdout=StringIO())


class StatusCatalogApiTests(AuthenticatedAPITestCase):
    expected_statuses = [
        {"tag": "created", "name": "Creada"},
        {"tag": "in_review", "name": "En revisión"},
        {"tag": "in_progress", "name": "En progreso"},
        {"tag": "paused", "name": "Pausada"},
        {"tag": "done", "name": "Finalizada"},
    ]

    def test_initial_statuses_exist_and_tags_are_unique(self):
        self.assertEqual(
            list(Status.objects.values("tag", "name")),
            self.expected_statuses,
        )
        self.assertTrue(Status._meta.get_field("tag").unique)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Status.objects.create(tag="created", name="Duplicate")

    def test_list_statuses_exposes_only_tags_and_names(self):
        response = self.client.get("/api/statuses/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.expected_statuses)
        self.assertTrue(
            all(set(status_data) == {"tag", "name"} for status_data in response.data)
        )

    def test_statuses_endpoint_is_documented_and_swagger_is_available(self):
        schema_response = self.client.get("/api/schema/")
        swagger_response = self.client.get("/api/docs/")

        self.assertEqual(schema_response.status_code, status.HTTP_200_OK)
        self.assertIn("/api/statuses/", schema_response.data["paths"])
        self.assertEqual(swagger_response.status_code, status.HTTP_200_OK)


class HealthCheckTests(APITestCase):
    def test_health_check(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {"status": "ok"})

    def test_cors_preflight_for_configured_origin(self):
        response = self.client.options(
            "/api/health/",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "http://localhost:5173",
        )


class RequestCreationApiTests(AuthenticatedAPITestCase):
    def test_list_requests_returns_nested_status_and_only_recent_requests(self):
        recent_request = Request.objects.create(
            title="Recent request",
            description="Created this week.",
            status=Status.objects.get(tag="in_review"),
        )
        old_request = Request.objects.create(
            title="Old request",
            description="Created earlier.",
            status=Status.objects.get(tag="created"),
        )
        Request.objects.filter(pk=old_request.pk).update(
            created_at=timezone.now() - timedelta(days=10),
        )

        response = self.client.get("/api/requests/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], recent_request.pk)
        self.assertEqual(
            response.data[0]["status"],
            {"tag": "in_review", "name": recent_request.status.name},
        )

    def test_list_requests_can_filter_by_date_range(self):
        requested = Request.objects.create(
            title="Filtered request",
            description="Inside requested date range.",
            status=Status.objects.get(tag="created"),
        )
        requested_date = timezone.localdate()
        response = self.client.get(
            "/api/requests/",
            {
                "start_date": requested_date.isoformat(),
                "end_date": requested_date.isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [requested.pk])

    def test_list_requests_rejects_invalid_date_range(self):
        response = self.client.get(
            "/api/requests/",
            {"start_date": "not-a-date"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_request_returns_created_request(self):
        response = self.client.post(
            "/api/requests/",
            {
                "title": "Review application",
                "description": "Review the submitted application.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Request.objects.count(), 1)

        request = Request.objects.get()
        self.assertEqual(response.data, RequestSerializer(request).data)
        self.assertEqual(response.data["title"], "Review application")
        self.assertEqual(
            response.data["description"],
            "Review the submitted application.",
        )
        self.assertEqual(
            response.data["status"],
            {"tag": "created", "name": request.status.name},
        )
        self.assertEqual(request.status.tag, "created")
        self.assertEqual(
            request.status_id,
            Status.objects.get(tag="created").pk,
        )
        self.assertIsNotNone(response.data["id"])
        self.assertIsNotNone(request.created_at)
        self.assertIsNotNone(request.updated_at)

    def test_client_cannot_choose_initial_status_or_catalog_id(self):
        for field, value in (
            ("status", "done"),
            ("status", 5),
            ("status_id", 5),
        ):
            with self.subTest(field=field, value=value):
                response = self.client.post(
                    "/api/requests/",
                    {
                        "title": "Review application",
                        "description": "Review the submitted application.",
                        field: value,
                    },
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(
                    response.data["status"],
                    {
                        "tag": "created",
                        "name": Status.objects.get(tag="created").name,
                    },
                )

    def test_used_status_cannot_be_deleted(self):
        request = Request.objects.create(
            title="Protected request",
            description="A request with an assigned status.",
            status=Status.objects.get(tag="created"),
        )

        with self.assertRaises(ProtectedError):
            request.status.delete()

    def test_invalid_payloads_do_not_create_requests(self):
        invalid_payloads = [
            {"description": "Missing title"},
            {"title": "Missing description"},
            {"title": "", "description": "A description"},
            {"title": "A title", "description": ""},
            {"title": "x" * 201, "description": "A description"},
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(
                    "/api/requests/",
                    payload,
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(Request.objects.count(), 0)


class RequestStatusUpdateApiTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.request = Request.objects.create(
            title="Review application",
            description="Review the submitted application.",
            status=Status.objects.get(tag="created"),
        )

    def test_allowed_transition_updates_only_the_status(self):
        response = self.client.patch(
            f"/api/requests/{self.request.pk}/",
            {"status": "in_review"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["status"],
            {
                "tag": "in_review",
                "name": Status.objects.get(tag="in_review").name,
            },
        )
        self.request.refresh_from_db()
        self.assertEqual(self.request.status.tag, "in_review")
        self.assertEqual(self.request.title, "Review application")
        self.assertEqual(
            self.request.description,
            "Review the submitted application.",
        )

    def test_invalid_transition_does_not_change_the_request(self):
        updated_at = self.request.updated_at
        response = self.client.patch(
            f"/api/requests/{self.request.pk}/",
            {"status": "done"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status.tag, "created")
        self.assertEqual(self.request.updated_at, updated_at)
        self.assertEqual(self.request.title, "Review application")
        self.assertEqual(
            self.request.description,
            "Review the submitted application.",
        )

    def test_paused_request_cannot_transition_directly_to_done(self):
        self.request.status = Status.objects.get(tag="paused")
        self.request.save(update_fields=["status"])

        response = self.client.patch(
            f"/api/requests/{self.request.pk}/",
            {"status": "done"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status.tag, "paused")

    def test_unknown_status_is_rejected(self):
        response = self.client.patch(
            f"/api/requests/{self.request.pk}/",
            {"status": "unknown"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status.tag, "created")

    def test_other_fields_and_missing_status_are_rejected(self):
        for payload in (
            {"status": "in_review", "title": "Altered title"},
            {"status": "in_review", "status_id": Status.objects.get(tag="done").pk},
            {"title": "Altered title"},
        ):
            with self.subTest(payload=payload):
                response = self.client.patch(
                    f"/api/requests/{self.request.pk}/",
                    payload,
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

        self.request.refresh_from_db()
        self.assertEqual(self.request.status.tag, "created")
        self.assertEqual(self.request.title, "Review application")

    def test_missing_request_returns_404(self):
        response = self.client.patch(
            "/api/requests/999999/",
            {"status": "in_review"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RequestStatusTransitionTests(SimpleTestCase):
    def test_complete_transition_matrix(self):
        statuses = (
            "created",
            "in_review",
            "in_progress",
            "paused",
            "done",
        )

        for current_status in statuses:
            for next_status in statuses:
                allowed = next_status in ALLOWED_STATUS_TRANSITIONS[current_status]
                with self.subTest(
                    current_status=current_status,
                    next_status=next_status,
                ):
                    if allowed:
                        validate_request_status_transition(current_status, next_status)
                    else:
                        with self.assertRaises(InvalidRequestStatusTransition):
                            validate_request_status_transition(
                                current_status,
                                next_status,
                            )


class RequestStatusDataMigrationTests(TransactionTestCase):
    migrate_from = [("api", "0002_request")]
    migrate_to = [("api", "0004_migrate_request_status")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        old_request_model = old_apps.get_model("api", "Request")
        old_request_model.objects.create(
            title="Existing request",
            description="Keep its previous status.",
            status="paused",
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.new_apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_request_keeps_its_status_tag(self):
        migrated_request = self.new_apps.get_model("api", "Request").objects.get(
            title="Existing request"
        )

        self.assertEqual(migrated_request.status_id, "paused")
        self.assertEqual(migrated_request.status.tag, "paused")


class RequestStatusForeignKeyMigrationTests(TransactionTestCase):
    migrate_from = [("api", "0004_migrate_request_status")]
    migrate_to = [("api", "0005_request_status_fk_numeric")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        old_request_model = old_apps.get_model("api", "Request")
        old_request_model.objects.create(
            title="Request before numeric FK",
            description="Keep its existing status.",
            status="paused",
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.new_apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_numeric_fk_preserves_request_status_and_catalog(self):
        RequestModel = self.new_apps.get_model("api", "Request")
        StatusModel = self.new_apps.get_model("api", "Status")
        migrated_request = RequestModel.objects.get(
            title="Request before numeric FK"
        )
        paused_status = StatusModel.objects.get(tag="paused")

        self.assertEqual(StatusModel.objects.count(), 5)
        self.assertEqual(migrated_request.status_id, paused_status.pk)
        self.assertEqual(migrated_request.status.tag, "paused")
