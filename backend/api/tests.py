import json

from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Item


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
