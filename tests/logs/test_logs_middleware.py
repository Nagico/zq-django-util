import importlib
from unittest.mock import MagicMock, patch

from django.test import override_settings
from rest_framework.test import APIRequestFactory, APITestCase

import zq_django_util.logs.threads
from zq_django_util.logs.middleware import APILoggerMiddleware


class APILoggerMiddlewareTestCase(APITestCase):
    @staticmethod
    def mock_get_response(*args, **kwargs):
        return "RESPONSE"

    @staticmethod
    async def mock_get_response_async(*args, **kwargs):
        return "RESPONSE"

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_init(self):
        middleware = APILoggerMiddleware(self.mock_get_response)
        middleware_async = APILoggerMiddleware(self.mock_get_response_async)

        self.assertFalse(middleware._is_coroutine)
        self.assertTrue(middleware_async._is_coroutine)

    @patch("zq_django_util.logs.threads.LOGGER_THREAD")
    def test_insert_log(
        self,
        mock_thread: MagicMock,
    ):
        importlib.reload(zq_django_util.logs.middleware)

        middleware = APILoggerMiddleware(self.mock_get_response)

        request = self.factory.get("/test")
        middleware.insert_log(request)

        mock_thread.put_log_data.assert_called_once_with(
            request,
            "RESPONSE",
            mock_thread.put_log_data.call_args[0][2],
            mock_thread.put_log_data.call_args[0][3],
        )

    @patch("zq_django_util.logs.threads.LOGGER_THREAD")
    async def test_insert_log_async(
        self,
        mock_thread: MagicMock,
    ):
        importlib.reload(zq_django_util.logs.middleware)

        middleware = APILoggerMiddleware(self.mock_get_response_async)

        request = self.factory.get("/test")
        await middleware.insert_log_async(request)

        mock_thread.put_log_data.assert_called_once_with(
            request,
            "RESPONSE",
            mock_thread.put_log_data.call_args[0][2],
            mock_thread.put_log_data.call_args[0][3],
        )

    @patch(
        "zq_django_util.logs.middleware.APILoggerMiddleware.insert_log_async"
    )
    @patch("zq_django_util.logs.middleware.APILoggerMiddleware.insert_log")
    @override_settings(DRF_LOGGER={"DATABASE": False})
    def test_call_disable(
        self,
        mock_insert_log: MagicMock,
        mock_insert_log_async: MagicMock,
    ):
        middleware = APILoggerMiddleware(self.mock_get_response)
        middleware(self.factory.get("/test"))

        mock_insert_log.assert_not_called()
        mock_insert_log_async.assert_not_called()

    @patch(
        "zq_django_util.logs.middleware.APILoggerMiddleware.insert_log_async"
    )
    @patch("zq_django_util.logs.middleware.APILoggerMiddleware.insert_log")
    @override_settings(DRF_LOGGER={"DATABASE": True})
    def test_call_enable(
        self,
        mock_insert_log: MagicMock,
        mock_insert_log_async: MagicMock,
    ):
        middleware = APILoggerMiddleware(self.mock_get_response)
        request = self.factory.get("/test")
        middleware(request)

        mock_insert_log.assert_called_once_with(request)
        mock_insert_log_async.assert_not_called()

    @patch(
        "zq_django_util.logs.middleware.APILoggerMiddleware.insert_log_async"
    )
    @patch("zq_django_util.logs.middleware.APILoggerMiddleware.insert_log")
    @override_settings(DRF_LOGGER={"DATABASE": True})
    async def test_call_enable_async(
        self,
        mock_insert_log: MagicMock,
        mock_insert_log_async: MagicMock,
    ):
        middleware = APILoggerMiddleware(self.mock_get_response_async)
        request = self.factory.get("/test")
        await middleware(request)

        mock_insert_log.assert_not_called()
        mock_insert_log_async.assert_called_once_with(request)
