from django.contrib.auth.hashers import make_password
from model_bakery import baker
from rest_framework.test import APIRequestFactory, APITestCase

from tests.models import User
from zq_django_util.exceptions import ApiException
from zq_django_util.response import ResponseType
from zq_django_util.utils.auth.serializers import (
    AbstractWechatLoginSerializer,
    OpenIdLoginSerializer,
    PasswordLoginSerializer,
)


class OpenIdLoginSerializerTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.openid = "openid"
        self.serializer = OpenIdLoginSerializer
        self.user = baker.make(User, is_active=True, openid=self.openid)

    def test_success(self):
        data = {"openid": self.openid}
        serializer = self.serializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["id"], self.user.pk)
        self.assertEqual(
            serializer.validated_data["username"], self.user.username
        )
        self.assertIn("access", serializer.validated_data)
        self.assertIn("refresh", serializer.validated_data)

    def test_openid_not_bind(self):
        data = {"openid": "-1"}
        serializer = self.serializer(data=data)
        with self.assertRaises(ApiException) as context:
            serializer.is_valid()
        self.assertEqual(
            context.exception.response_type, ResponseType.ThirdLoginFailed
        )


class AbstractWechatLoginSerializerTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.openid = "openid"
        self.serializer = AbstractWechatLoginSerializer
        self.user = baker.make(User, is_active=True, openid=self.openid)

    def test_abstract_wechat_login_serializer(self):
        with self.assertRaises(NotImplementedError):
            self.serializer(data={"code": "123"}).is_valid()


class PasswordLoginSerializerTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.username = "foo"
        self.password = "bar"
        self.serializer = PasswordLoginSerializer
        self.user = baker.make(
            User,
            is_active=True,
            username=self.username,
            password=make_password(self.password),
        )

    def test_success(self):
        data = {"username": self.username, "password": self.password}
        serializer = self.serializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["id"], self.user.pk)
        self.assertEqual(
            serializer.validated_data["username"], self.user.username
        )
        self.assertIn("access", serializer.validated_data)
        self.assertIn("refresh", serializer.validated_data)
