from django.test import override_settings
from model_bakery import baker
from rest_framework.test import APITestCase

from tests.models import User


class CacheMixinTestCase(APITestCase):
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
    def test_list(self):
        self.assertEqual(
            self.client.get("/users/").data,
            self.client.get("/users/").data,
        )

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        ROOT_URLCONF="tests.sites.urls",
    )
    def test_list_with_params(self):
        self.assertEqual(
            self.client.get("/users/", {"phone": self.phone}).data,
            self.client.get("/users/", {"phone": self.phone}).data,
        )

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        ROOT_URLCONF="tests.sites.urls",
    )
    def test_retrieve(self):
        user = baker.make(User)
        self.assertEqual(
            self.client.get(f"/users/{user.pk}/").data,
            self.client.get(f"/users/{user.pk}/").data,
        )

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
        ROOT_URLCONF="tests.sites.urls",
    )
    def test_list_no_page(self):
        self.assertEqual(
            self.client.get("/users_no_page/").data,
            self.client.get("/users_no_page/").data,
        )
