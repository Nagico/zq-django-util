import importlib
from threading import Thread
from time import sleep
from unittest.mock import MagicMock, patch

from rest_framework.test import APITestCase

from zq_django_util.logs import threads


class LogThreadTestCase(APITestCase):
    LOG_THREAD_NAME = "log_thread"

    @patch(
        "zq_django_util.logs.utils.is_api_logger_enabled", return_value=False
    )
    def test_not_enable(
        self,
        is_api_logger_enabled_mock: MagicMock,
    ):
        importlib.reload(threads)
        self.assertIsNone(threads.LOGGER_THREAD)

    @patch("zq_django_util.logs.utils.is_api_logger_enabled", return_value=True)
    @patch("zq_django_util.logs.handler.HandleLogAsync")
    def test_enable(
        self,
        handle_log_async_mock: MagicMock,
        is_api_logger_enabled_mock: MagicMock,
    ):
        importlib.reload(threads)
        self.assertIsNotNone(threads.LOGGER_THREAD)
        self.assertEqual(threads.LOGGER_THREAD.name, self.LOG_THREAD_NAME)
        self.assertTrue(threads.LOGGER_THREAD.is_alive())

    class MockThread(Thread):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.flag = True

        def run(self):
            while self.flag:
                sleep(0.1)

        def stop(self):
            self.flag = False

    @patch("zq_django_util.logs.utils.is_api_logger_enabled", return_value=True)
    @patch("zq_django_util.logs.handler.HandleLogAsync")
    def test_enable_same_name(
        self,
        handle_log_async_mock: MagicMock,
        is_api_logger_enabled_mock: MagicMock,
    ):
        t = self.MockThread()
        t.name = self.LOG_THREAD_NAME
        t.daemon = True
        t.start()

        importlib.reload(threads)
        self.assertTrue(threads.already_exists)
        self.assertIsNone(threads.LOGGER_THREAD)

        t.stop()
        t.join()
