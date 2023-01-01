from django.test import override_settings
from model_bakery import baker
from rest_framework.test import APITestCase

from tests.models import User


class GlobalPageNumberPaginationTestCase(APITestCase):
    def setUp(self):
        self.phone = "12312341234"

        baker.make(User, _quantity=10)
        baker.make(User, _quantity=10, phone=self.phone)

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        ROOT_URLCONF="tests.sites.urls",
    )
    def test_list_page(self):
        data = self.client.get("/users/?page=2&page_size=5").data
        self.assertEqual(data["count"], 20)
        self.assertEqual(
            data["next"], "http://testserver/users/?page=3&page_size=5"
        )
        self.assertEqual(
            data["previous"], "http://testserver/users/?page_size=5"
        )
        self.assertEqual(len(data["results"]), 5)
