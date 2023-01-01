from unittest.mock import MagicMock, patch

from django.test import override_settings
from model_bakery import baker
from rest_framework.test import APITestCase
from rest_framework_simplejwt.exceptions import TokenError

from tests.models import User
from zq_django_util.exceptions import ApiException
from zq_django_util.response import ResponseType
from zq_django_util.utils.auth.views import OpenIdLoginView


class OpenIdLoginSerializerTestCase(APITestCase):
    def setUp(self):
        self.openid = "openid"
        self.view = OpenIdLoginView
        self.user = baker.make(User, is_active=True, openid=self.openid)

    @override_settings(ROOT_URLCONF="tests.auth.urls")
    def test_get_token(self):
        response = self.client.post("/login/openid/", {"openid": self.openid})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["username"], self.user.username)

    @override_settings(ROOT_URLCONF="tests.auth.urls")
    @patch("zq_django_util.utils.auth.views.OpenIdLoginView.get_serializer")
    def test_get_token_fail(
        self,
        mock_get_serializer: MagicMock,
    ):
        mock_get_serializer.return_value.is_valid.side_effect = TokenError

        with self.assertRaises(ApiException) as context:
            self.client.post("/login/openid/", {"openid": self.openid})

        self.assertEqual(
            context.exception.response_type, ResponseType.ThirdLoginFailed
        )
