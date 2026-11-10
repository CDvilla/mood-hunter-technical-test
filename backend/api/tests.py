import json

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from api.domain import (
    ALLOWED_STATUS_TRANSITIONS,
    InvalidRequestStatusTransition,
    validate_request_status_transition,
)
from api.models import Item, Request
from api.serializers import RequestSerializer


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


class ItemApiTests(APITestCase):
    def test_create_and_list_items(self):
        create_response = self.client.post(
            "/api/items/",
            {"name": "First item", "description": "An example"},
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 1)

        list_response = self.client.get("/api/items/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data[0]["name"], "First item")

    def test_retrieve_update_and_delete_item(self):
        item = Item.objects.create(name="Original item")

        retrieve_response = self.client.get(f"/api/items/{item.id}/")
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)

        update_response = self.client.patch(
            f"/api/items/{item.id}/",
            {"name": "Updated item"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["name"], "Updated item")

        delete_response = self.client.delete(f"/api/items/{item.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Item.objects.filter(id=item.id).exists())


class RequestCreationApiTests(APITestCase):
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
        self.assertEqual(response.data["status"], Request.Status.CREATED)
        self.assertIsNotNone(response.data["id"])
        self.assertIsNotNone(request.created_at)
        self.assertIsNotNone(request.updated_at)

    def test_client_cannot_choose_initial_status(self):
        response = self.client.post(
            "/api/requests/",
            {
                "title": "Review application",
                "description": "Review the submitted application.",
                "status": Request.Status.DONE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Request.Status.CREATED)

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


class RequestStatusTransitionTests(SimpleTestCase):
    def test_complete_transition_matrix(self):
        statuses = Request.Status.values

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
