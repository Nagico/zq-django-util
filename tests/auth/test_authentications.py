from model_bakery import baker
from rest_framework.test import APIRequestFactory, APITestCase

from tests.models import User
from zq_django_util.exceptions import ApiException
from zq_django_util.response import ResponseType
from zq_django_util.utils.auth.authentications import (
    ActiveUserAuthentication,
    NormalUserAuthentication,
)


class ActiveUserAuthenticationTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.authentication = ActiveUserAuthentication()
        self.user = baker.make(User, is_active=True)

    def test_get_user(self):
        context = {"user_id": self.user.id}
        self.assertEqual(self.authentication.get_user(context), self.user)

    def test_get_user_claim_error(self):
        context = {"id": self.user.id}
        with self.assertRaises(ApiException) as exc_context:
            self.authentication.get_user(context)
        self.assertEqual(
            exc_context.exception.response_type, ResponseType.TokenInvalid
        )

    def test_get_user_not_exists(self):
        context = {"user_id": -1}
        with self.assertRaises(ApiException) as exc_context:
            self.authentication.get_user(context)
        self.assertEqual(
            exc_context.exception.response_type, ResponseType.ResourceNotFound
        )

    def test_check_activate(self):
        self.authentication.check_activate(self.user)

    def test_check_activate_error(self):
        user = baker.prepare(User, is_active=False)
        with self.assertRaises(ApiException) as exc_context:
            self.authentication.check_activate(user)
        self.assertEqual(
            exc_context.exception.response_type, ResponseType.NotActive
        )


class NormalUserAuthenticationTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.authentication = NormalUserAuthentication()
        self.user = baker.make(User, is_active=True)

    def test_check_activate(self):
        self.authentication.check_activate(self.user)
        user = baker.prepare(User, is_active=False)
        self.authentication.check_activate(user)
