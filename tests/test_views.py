from django.contrib.auth.hashers import make_password
from model_bakery import baker
from rest_framework.test import APITestCase

from tests.models import User


class APIRootViewSetTestCase(APITestCase):
    def setUp(self):
        self.username = "foo"
        self.password = "bar"
        self.user = baker.make(
            User,
            is_active=True,
            username=self.username,
            password=make_password(self.password),
        )

    def test_anonymous(self):
        data = self.client.get("").data
        res = dict(
            user=None,
            time=data["time"],
        )
        self.assertDictEqual(data, res)

    def test_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        data = self.client.get("").data
        res = dict(
            user=dict(
                id=self.user.pk,
                username=self.user.username,
                is_active=self.user.is_active,
                is_superuser=self.user.is_superuser,
            ),
            time=data["time"],
        )
        self.assertDictEqual(data, res)
