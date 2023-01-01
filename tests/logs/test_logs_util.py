from django.test import override_settings
from rest_framework.test import APIRequestFactory, APITestCase

from zq_django_util.logs.utils import (
    database_log_enabled,
    get_client_ip,
    get_headers,
    is_api_logger_enabled,
    mask_sensitive_data,
)


class LogUtilTestCase(APITestCase):
    def test_get_headers(self):
        headers = {
            "HOST": "localhost:8000",
            "CONNECTION": "keep-alive",
            "ACCEPT": "application/json, text/plain, */*",
            "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "ORIGIN": "http://localhost:3000",
            "SEC_FETCH_SITE": "same-origin",
            "SEC_FETCH_MODE": "cors",
            "SEC_FETCH_DEST": "empty",
            "REFERER": "http://localhost:3000/",
            "ACCEPT_ENCODING": "gzip, deflate, br",
            "ACCEPT_LANGUAGE": "en-US,en;q=0.9",
        }

        request = APIRequestFactory().get("/api/")
        request.META = {f"HTTP_{key}": value for key, value in headers.items()}
        request.META.update(
            {
                "REMOTE_ADDR": "localhost:8000",
            }
        )

        parser_header = get_headers(request)
        self.assertDictEqual(parser_header, headers)

    def test_get_client_ip_REMOTE_ADDR(self):
        request = APIRequestFactory().get("/api/")
        request.META = {
            "REMOTE_ADDR": "localhost:8000",
        }

        ip = get_client_ip(request)
        self.assertEqual(ip, "localhost:8000")

    def test_get_client_ip_X_FORWARDED_FOR(self):
        request = APIRequestFactory().get("/api/")
        request.META = {
            "HTTP_X_FORWARDED_FOR": "localhost:8001,localhost:8002",
            "REMOTE_ADDR": "localhost:8000",
        }

        ip = get_client_ip(request)
        self.assertEqual(ip, "localhost:8001")

    def test_get_client_ip_X_FORWARDED_FOR_empty(self):
        request = APIRequestFactory().get("/api/")
        request.META = {
            "HTTP_X_FORWARDED_FOR": "",
            "REMOTE_ADDR": "localhost:8000",
        }

        ip = get_client_ip(request)
        self.assertEqual(ip, "localhost:8000")

    def test_get_client_ip_X_FORWARDED_FOR_exception(self):
        request = APIRequestFactory().get("/api/")
        request.META = {
            "HTTP_X_FORWARDED_FOR": 123,
        }

        ip = get_client_ip(request)
        self.assertEqual(ip, "")

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": False,
        }
    )
    def test_enabled(self):
        self.assertTrue(is_api_logger_enabled())
        self.assertTrue(database_log_enabled())

    @override_settings(
        DRF_LOGGER={
            "DATABASE": False,
            "SIGNAL": False,
        }
    )
    def test_disabled(self):
        self.assertFalse(is_api_logger_enabled())
        self.assertFalse(database_log_enabled())

    @override_settings(
        DRF_LOGGER={
            "SENSITIVE_KEYS": ["password"],
        }
    )
    def test_mask_sensitive_data_dict(self):
        username = "test"
        password = "123456"

        data = {
            "password": password,
            "list": [
                {
                    "password": password,
                },
                {
                    "password": password,
                },
                {
                    "username": username,
                },
            ],
            "dict": {
                "password": password,
                "username": username,
            },
        }

        masked_data = {
            "password": f"***FILTERED*** (len: {len(password)})",
            "list": [
                {
                    "password": f"***FILTERED*** (len: {len(password)})",
                },
                {
                    "password": f"***FILTERED*** (len: {len(password)})",
                },
                {
                    "username": username,
                },
            ],
            "dict": {
                "password": f"***FILTERED*** (len: {len(password)})",
                "username": username,
            },
        }

        self.assertDictEqual(masked_data, mask_sensitive_data(data))

    @override_settings(
        DRF_LOGGER={
            "SENSITIVE_KEYS": ["password"],
        }
    )
    def test_mask_sensitive_data_not_dict(self):
        data = "password"

        self.assertEqual(data, mask_sensitive_data(data))
