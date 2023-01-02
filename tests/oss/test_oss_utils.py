import base64
import importlib
from unittest.mock import MagicMock, patch

from Crypto.PublicKey import RSA
from django.core.cache import cache
from django.test import override_settings
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase

import zq_django_util
from zq_django_util.utils.oss.utils import (
    _get_pub_key_online,
    check_callback_signature,
    get_pub_key,
    get_random_name,
    get_token,
    split_file_name,
)


class FilenameUtilTestCase(APITestCase):
    random_rex = r"[0-9]{14}_[0-9]{4}"

    def test_split_file_name_normal(self):
        name, ext = split_file_name("test.txt")
        self.assertEqual(name, "test")
        self.assertEqual(ext, "txt")

    def test_split_file_name_no_ext(self):
        name, ext = split_file_name("test")
        self.assertEqual(name, "test")
        self.assertEqual(ext, "")

    def test_split_file_name_multi_ext(self):
        name, ext = split_file_name("test.txt.txt")
        self.assertEqual(name, "test.txt")
        self.assertEqual(ext, "txt")

    def test_split_file_name_multi_dot(self):
        name, ext = split_file_name("test..txt")
        self.assertEqual(name, "test.")
        self.assertEqual(ext, "txt")

    def test_split_file_name_multi_dot_multi_ext(self):
        name, ext = split_file_name("test..txt.txt")
        self.assertEqual(name, "test..txt")
        self.assertEqual(ext, "txt")

    def test_split_file_name_no_name(self):
        name, ext = split_file_name(".txt")
        self.assertEqual(name, "")
        self.assertEqual(ext, "txt")

    def test_split_file_name_no_name_no_ext(self):
        name, ext = split_file_name(".")
        self.assertEqual(name, "")
        self.assertEqual(ext, "")

    def test_split_file_name_empty(self):
        name, ext = split_file_name("")
        self.assertEqual(name, "")
        self.assertEqual(ext, "")

    def test_random_name(self):
        name = get_random_name("test.txt")
        self.assertRegex(name, f"^{self.random_rex}.txt$")

    def test_random_name_no_ext(self):
        name = get_random_name("test")
        self.assertRegex(name, f"^{self.random_rex}$")

    def test_random_name_multi_ext(self):
        name = get_random_name("test.txt.txt")
        self.assertRegex(name, f"^{self.random_rex}.txt$")

    def test_random_name_multi_dot(self):
        name = get_random_name("test..txt")
        self.assertRegex(name, f"^{self.random_rex}.txt$")

    def test_random_name_multi_dot_multi_ext(self):
        name = get_random_name("test..txt.txt")
        self.assertRegex(name, f"^{self.random_rex}.txt$")

    def test_random_name_no_name(self):
        name = get_random_name(".txt")
        self.assertRegex(name, f"^{self.random_rex}.txt$")

    def test_random_name_no_name_no_ext(self):
        name = get_random_name(".")
        self.assertRegex(name, f"^{self.random_rex}$")

    def test_random_name_empty(self):
        name = get_random_name("")
        self.assertRegex(name, f"^{self.random_rex}$")


class CallbackUtilTestCase(APITestCase):
    access_key_id = "access_key_id"
    access_key_secret = "access_key_secret"
    bucket_name = "bucket"
    endpoint = "https://oss-cn-shanghai.aliyuncs.com"

    @override_settings(
        ALIYUN_OSS={
            "ACCESS_KEY_ID": access_key_id,
            "ACCESS_KEY_SECRET": access_key_secret,
            "ENDPOINT": endpoint,
            "BUCKET_NAME": bucket_name,
            "URL_EXPIRE_SECOND": 60 * 60 * 24 * 30,
            "TOKEN_EXPIRE_SECOND": 60,
            "MAX_SIZE_MB": 100,
        }
    )
    def test_get_token(self):
        token = get_token(
            key="dir/test.txt",
            callback={
                "callbackUrl": "http://testserver/callback/",
                "callbackBody": "file=${object}&size=${size}",
                "callbackBodyType": "application/x-www-form-urlencoded",
            },
        )
        self.assertEqual(token["OSSAccessKeyId"], self.access_key_id)
        self.assertEqual(
            token["host"], "https://bucket.oss-cn-shanghai.aliyuncs.com"
        )
        self.assertEqual(token["key"], "dir/test.txt")
        self.assertIn("policy", token)
        self.assertIn("signature", token)
        self.assertIn("callback", token)
        self.assertIn("expire", token)

    @patch("urllib.request.urlopen")
    def test__get_pub_key_online(self, mock_urlopen: MagicMock):
        importlib.reload(zq_django_util.utils.oss.utils)
        mock_urlopen.return_value.read.return_value = b"pub_key"

        url = "https://testserver/"
        pub_key = _get_pub_key_online(url)
        self.assertEqual(pub_key, b"pub_key")

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
    )
    @patch("zq_django_util.utils.oss.utils._get_pub_key_online")
    def test_get_pub_key(self, mock_get_online: MagicMock):
        mock_get_online.return_value = "pub_key"
        res = get_pub_key("url")
        self.assertEqual(res, "pub_key")
        self.assertEqual(cache.get("oss:pub_key:url"), "pub_key")

    @patch("django.core.cache.cache")
    def test_get_pub_key_cache(self, mock_cache: MagicMock):
        importlib.reload(zq_django_util.utils.oss.utils)
        mock_cache.get.side_effect = ValueError()
        with patch(
            "zq_django_util.utils.oss.utils._get_pub_key_online"
        ) as mock_get_online:
            mock_get_online.return_value = "pub_key"

            res = get_pub_key("url")
            self.assertEqual(res, "pub_key")

    @patch("Crypto.Signature.pkcs1_15.PKCS115_SigScheme")
    @patch("zq_django_util.utils.oss.utils.get_pub_key")
    def test_check_callback_signature_simple_path(
        self, mock_get_pub_key: MagicMock, mock_pkcs1_15: MagicMock
    ):
        pub_key_url = "https://gosspublic.alicdn.com/url"
        authorization = "authorization"

        key = RSA.generate(1024)

        mock_get_pub_key.return_value = key.publickey().export_key()

        request = Request(
            APIRequestFactory().post(
                path="/test/",
                data={"key": "value"},
                HTTP_AUTHORIZATION=base64.b64encode(authorization.encode()),
                HTTP_X_OSS_PUB_KEY_URL=base64.b64encode(pub_key_url.encode()),
            )
        )

        res = check_callback_signature(request)
        self.assertTrue(res)

    @patch("Crypto.Signature.pkcs1_15.PKCS115_SigScheme")
    @patch("zq_django_util.utils.oss.utils.get_pub_key")
    def test_check_callback_signature_query_path(
        self, mock_get_pub_key: MagicMock, mock_pkcs1_15: MagicMock
    ):
        pub_key_url = "https://gosspublic.alicdn.com/url"
        authorization = "authorization"

        key = RSA.generate(1024)

        mock_get_pub_key.return_value = key.publickey().export_key()

        request = Request(
            APIRequestFactory().post(
                path="/test/?foo=bar",
                data={"key": "value"},
                HTTP_AUTHORIZATION=base64.b64encode(authorization.encode()),
                HTTP_X_OSS_PUB_KEY_URL=base64.b64encode(pub_key_url.encode()),
            )
        )

        res = check_callback_signature(request)
        self.assertTrue(res)

    def test_check_callback_signature_header_empty(self):
        request = Request(
            APIRequestFactory().post(
                path="/test/?foo=bar", data={"key": "value"}
            )
        )
        res = check_callback_signature(request)
        self.assertFalse(res)

    @patch("Crypto.Signature.pkcs1_15.PKCS115_SigScheme")
    @patch("zq_django_util.utils.oss.utils.get_pub_key")
    def test_check_callback_signature_header_parse_error(
        self, mock_get_pub_key: MagicMock, mock_pkcs1_15: MagicMock
    ):
        pub_key_url = "https://gosspublic.alicdn.com/url"
        authorization = "authorization"

        key = RSA.generate(1024)

        mock_get_pub_key.return_value = key.publickey().export_key()

        request = Request(
            APIRequestFactory().post(
                path="/test/?foo=bar",
                data={"key": "value"},
                HTTP_AUTHORIZATION=authorization,
                HTTP_X_OSS_PUB_KEY_URL=pub_key_url,
            )
        )

        res = check_callback_signature(request)
        self.assertFalse(res)

    @patch("Crypto.Signature.pkcs1_15.PKCS115_SigScheme")
    @patch("zq_django_util.utils.oss.utils.get_pub_key")
    def test_check_callback_signature_header_pub_key_url_invalid(
        self, mock_get_pub_key: MagicMock, mock_pkcs1_15: MagicMock
    ):
        pub_key_url = "https://url"
        authorization = "authorization"

        key = RSA.generate(1024)

        mock_get_pub_key.return_value = key.publickey().export_key()

        request = Request(
            APIRequestFactory().post(
                path="/test/?foo=bar",
                data={"key": "value"},
                HTTP_AUTHORIZATION=base64.b64encode(authorization.encode()),
                HTTP_X_OSS_PUB_KEY_URL=base64.b64encode(pub_key_url.encode()),
            )
        )

        res = check_callback_signature(request)
        self.assertFalse(res)
