from model_bakery import baker
from rest_framework.test import APIRequestFactory, APITestCase

from tests.models import User
from zq_django_util.utils.auth.backends import OpenIdBackend
from zq_django_util.utils.auth.exceptions import (
    OpenIdNotBound,
    OpenIdNotProvided,
)


class OpenIdBackendTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.backend = OpenIdBackend()

    def test_authenticate_login(self):
        openid = "openid"

        user = User.objects.create(username="test", openid=openid)
        request = self.factory.request()
        auth_user = self.backend.authenticate(request, openid=openid)
        self.assertEqual(auth_user, user)

    def test_authenticate_login_no_openid(self):
        request = self.factory.request()

        self.assertIsNone(self.backend.authenticate(request))

    def test_authenticate_no_user(self):
        openid = "openid"
        request = self.factory.request()

        self.assertIsNone(self.backend.authenticate(request, openid=openid))

    def test_authenticate_login_no_openid_raise_exception(self):
        request = self.factory.request()

        with self.assertRaises(OpenIdNotProvided):
            self.backend.authenticate(request, raise_exception=True)

    def test_authenticate_no_user_raise_exception(self):
        openid = "openid"
        request = self.factory.request()

        with self.assertRaises(OpenIdNotBound):
            self.backend.authenticate(
                request, openid=openid, raise_exception=True
            )

    def test_get_user_exists(self):
        user = baker.make(User)
        self.assertEqual(self.backend.get_user(user.id), user)

    def test_get_user_not_exists(self):
        self.assertIsNone(self.backend.get_user(-1))
