import time
from time import sleep
from typing import Optional
from unittest.mock import MagicMock, PropertyMock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.temp import TemporaryFile
from django.db import OperationalError
from django.test import override_settings
from model_bakery import baker
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from zq_django_util.exceptions import ApiException
from zq_django_util.logs.handler import HandleLogAsync
from zq_django_util.logs.models import ExceptionLog, RequestLog
from zq_django_util.response import ResponseType
from zq_django_util.response.types import ApiExceptionResponse


class HandleLogAsyncTestCase(APITestCase):
    User = get_user_model()

    def create_context(
        self,
        url: str = "/api/",
        user: Optional[str | User] = None,
        token: Optional[str] = None,
        exception: Optional[Exception] = None,
        jwt: bool = False,
    ) -> (Request, ApiExceptionResponse, float):
        if user is None:
            user = AnonymousUser()
        elif isinstance(user, str):
            username = user
            user = self.User.objects.filter(username=username).first()
            if user is None:
                user = self.User.objects.create(username=username)

        if user.is_authenticated and jwt:
            token = token or str(RefreshToken.for_user(user).access_token)

        if jwt and user.is_authenticated:
            request = Request(
                APIRequestFactory().get(
                    url, HTTP_AUTHORIZATION=f"Bearer {token}"
                )
            )
        else:
            request = Request(APIRequestFactory().get(url))

        request.user = user

        client = APIClient()
        if jwt and user.is_authenticated:
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        client.force_authenticate(user=user)
        response: ApiExceptionResponse = client.get(url)

        response.api_request_data = request.data
        response.exception = False

        if exception is not None:
            response.exception = True
            response.exception_data = exception

        return request, response, time.time()

    @override_settings(DRF_LOGGER={"QUEUE_MAX_SIZE": 5})
    def test_put_log_data(self):
        context = self.create_context(user="test")

        handler = HandleLogAsync()
        handler.put_log_data(*context)

        self.assertEqual(handler._queue.qsize(), 1)

    @override_settings(DRF_LOGGER={"QUEUE_MAX_SIZE": 2})
    @patch("zq_django_util.logs.handler.HandleLogAsync._start_log_parse")
    def test_put_log_data_full(
        self,
        start_log_parse_mock: MagicMock,
    ):
        context = self.create_context(user="test")

        handler = HandleLogAsync()
        handler.put_log_data(*context)

        start_log_parse_mock.assert_not_called()

        handler.put_log_data(*context)
        start_log_parse_mock.assert_called_once()

    @override_settings(
        DRF_LOGGER={
            "INTERVAL": 0.1,
        }
    )
    @patch("zq_django_util.logs.handler.HandleLogAsync._start_log_parse")
    def test_thread_control(
        self,
        start_log_parse_mock: MagicMock,
    ):
        with HandleLogAsync() as t:
            self.assertTrue(t.is_alive())

        self.assertFalse(t.is_alive())

    @override_settings(
        DRF_LOGGER={
            "INTERVAL": 0.5,
        }
    )
    @patch("zq_django_util.logs.handler.HandleLogAsync._start_log_parse")
    def test_start_queue_process(
        self,
        start_log_parse_mock: MagicMock,
    ):
        with HandleLogAsync() as t:
            t.put_log_data(*self.create_context(user="test"))
            self.assertEqual(t._queue.qsize(), 1)
            start_log_parse_mock.assert_not_called()
            sleep(0.7)
            start_log_parse_mock.assert_called()

    @override_settings(
        DRF_LOGGER={
            "DATABASE": False,
            "SIGNAL": False,
        }
    )
    def test_prepare_request_log_disable(self):
        handler = HandleLogAsync()
        log_data = handler.prepare_request_log(
            *self.create_context(user="test")
        )

        self.assertIsNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_prepare_request_log_skip_admin(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/admin/"))
        log_data = handler.prepare_request_log(
            request, ApiExceptionResponse(), time.time()
        )

        self.assertIsNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_prepare_request_log_skip_debug(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/__debug__/"))

        log_data = handler.prepare_request_log(
            request, ApiExceptionResponse(), time.time()
        )

        self.assertIsNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
            "SKIP_URL_NAME": ["test-list"],
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_prepare_request_log_skip_custom_url_name(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))

        log_data = handler.prepare_request_log(
            request, ApiExceptionResponse(), time.time()
        )

        self.assertIsNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
            "SKIP_NAMESPACE": ["namespace"],
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_prepare_request_log_skip_custom_namespace(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/namespace/"))

        log_data = handler.prepare_request_log(
            request, ApiExceptionResponse(), time.time()
        )

        self.assertIsNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_prepare_request_log_not_skip_status_code_by_default(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))
        response = ApiExceptionResponse()
        response.status_code = 200

        log_data = handler.prepare_request_log(request, response, time.time())

        self.assertIsNotNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
            "STATUS_CODES": [500, 400],
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_prepare_request_log_not_skip_status_code_by_setting(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))
        response = ApiExceptionResponse()
        response.status_code = 500

        log_data = handler.prepare_request_log(request, response, time.time())

        self.assertIsNotNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
            "STATUS_CODES": [500, 400],
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_prepare_request_log_skip_status_code_by_setting(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))
        response = ApiExceptionResponse()
        response.status_code = 200

        log_data = handler.prepare_request_log(request, response, time.time())

        self.assertIsNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_prepare_request_log_not_skip_method_by_default(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))
        response = ApiExceptionResponse()
        response.status_code = 200

        log_data = handler.prepare_request_log(request, response, time.time())

        self.assertIsNotNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
            "METHODS": ["GET"],
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_prepare_request_log_not_skip_method_by_setting(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))
        response = ApiExceptionResponse()
        response.status_code = 200

        log_data = handler.prepare_request_log(request, response, time.time())

        self.assertIsNotNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
            "METHODS": ["POST"],
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_prepare_request_log_skip_method_by_setting(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))
        response = ApiExceptionResponse()
        response.status_code = 200

        log_data = handler.prepare_request_log(request, response, time.time())

        self.assertIsNone(log_data)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_user_id_with_jwt(self):
        handler = HandleLogAsync()
        user = self.User.objects.create(username="test", password="test")
        context = self.create_context(url="test", user=user, jwt=True)
        log_data = handler.get_request_log_data(*context)

        self.assertEqual(log_data["user"], user.id)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_user_id_with_session(self):
        handler = HandleLogAsync()
        user = self.User.objects.create(username="test", password="test")
        context = self.create_context(url="test", user=user, jwt=False)
        log_data = handler.get_request_log_data(*context)

        self.assertEqual(log_data["user"], user.id)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_user_id_not_authenticated(self):
        handler = HandleLogAsync()
        context = self.create_context(url="test")
        log_data = handler.get_request_log_data(*context)

        self.assertIsNone(log_data["user"])

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_user_id_wrong_jwt(self):
        handler = HandleLogAsync()
        context = self.create_context(
            url="test", user="test", jwt=True, token="123"
        )
        log_data = handler.get_request_log_data(*context)

        self.assertIsNone(log_data["user"])

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_request_data(self):
        handler = HandleLogAsync()
        with TemporaryFile() as fp:
            fp.write(b"test")
            fp.seek(0)
            request = Request(
                APIRequestFactory().post(
                    "/test/?foo=bar",
                    {"test": "test", "file": fp},
                )
            )
            response = ApiExceptionResponse()
            response.status_code = 200

            data = MultiPartParser().parse(
                stream=request.stream,
                media_type=request.content_type,
                parser_context={"request": request, "view": None},
            )

            response.api_request_data = data.files
            response.api_request_data.update(data.data)

            log_data = handler.get_request_log_data(
                request, response, time.time()
            )

            self.assertEqual(log_data["content_type"], request.content_type)
            self.assertEqual(log_data["method"], request.method)
            self.assertDictEqual(log_data["query_param"], {"foo": "bar"})
            self.assertDictEqual(log_data["request_body"], {"test": "test"})
            self.assertDictEqual(
                log_data["file_data"],
                {
                    "file": {
                        "name": data.files["file"].name,
                        "size": data.files["file"].size,
                        "content_type": data.files["file"].content_type,
                        "content_type_extra": data.files[
                            "file"
                        ].content_type_extra,
                    }
                },
            )

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_response_byte_data(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))
        response = self.client.get("/test/")
        response.status_code = 200
        response.headers["Content-Type"] = "application/json"
        response.content = b'{"test": "test"}'

        log_data = handler.get_request_log_data(request, response, time.time())

        self.assertEqual(log_data["response"], {"test": "test"})
        self.assertEqual(log_data["status_code"], response.status_code)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_response_str_data(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))

        response = self.client.get("/test/")
        response.status_code = 200
        response.headers["Content-Type"] = "application/vnd.api+json"

        with patch(
            "rest_framework.response.Response.content",
            new_callable=PropertyMock,
        ) as mock:
            mock.return_value = '{"test": "test"}'
            log_data = handler.get_request_log_data(
                request, response, time.time()
            )

            self.assertEqual(log_data["response"], {"test": "test"})
            self.assertEqual(log_data["status_code"], response.status_code)

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_response_streaming(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))
        response = self.client.get("/test/")
        response.status_code = 200
        response.headers["Content-Type"] = "application/json"
        response.content = {"test": "test"}
        response.streaming = True

        log_data = handler.get_request_log_data(request, response, time.time())

        self.assertEqual(log_data["response"], {"__content__": "streaming"})

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_response_gzip(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))
        response = self.client.get("/test/")
        response.status_code = 200
        response.headers["Content-Type"] = "application/gzip"
        response.content = b'{"test": "test"}'

        log_data = handler.get_request_log_data(request, response, time.time())

        self.assertEqual(log_data["response"], {"__content__": "gzip file"})

    @override_settings(
        DRF_LOGGER={
            "DATABASE": True,
            "SIGNAL": True,
        },
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_response_parse_error(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/"))
        response = self.client.get("/test/")
        response.status_code = 200
        response.headers["Content-Type"] = "application/json"
        response.content = b'{"test": }'

        log_data = handler.get_request_log_data(request, response, time.time())

        self.assertEqual(log_data["response"], {"__content__": "parse error"})

    @override_settings(
        DRF_LOGGER={"DATABASE": True, "SIGNAL": True, "PATH_TYPE": "ABSOLUTE"},
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_url_ABSOLUTE(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/?foo=bar"))
        response = ApiExceptionResponse()
        response.status_code = 200

        log_data = handler.get_request_log_data(request, response, time.time())

        self.assertEqual(log_data["url"], "http://testserver/test/?foo=bar")

    @override_settings(
        DRF_LOGGER={"DATABASE": True, "SIGNAL": True, "PATH_TYPE": "FULL_PATH"},
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_url_FULL_PATH(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/?foo=bar"))
        response = ApiExceptionResponse()
        response.status_code = 200

        log_data = handler.get_request_log_data(request, response, time.time())

        self.assertEqual(log_data["url"], "/test/?foo=bar")

    @override_settings(
        DRF_LOGGER={"DATABASE": True, "SIGNAL": True, "PATH_TYPE": "RAW_URI"},
        ROOT_URLCONF="tests.logs.urls",
    )
    def test_get_request_log_data_url_DEFAULT(self):
        handler = HandleLogAsync()
        request = Request(APIRequestFactory().get("/test/?foo=bar"))
        response = ApiExceptionResponse()
        response.status_code = 200

        log_data = handler.get_request_log_data(request, response, time.time())

        self.assertEqual(log_data["url"], "http://testserver/test/?foo=bar")

    def test_prepare_exception_log(self):
        handler = HandleLogAsync()
        exception = ApiException(ResponseType.ServerError)
        exception.event_id = "event_id"
        context = self.create_context(exception=exception)
        try:
            raise exception
        except ApiException as exc:
            log_data = handler.prepare_exception_log(*context)

            exp_data = dict(
                exp_id=exc.eid,
                event_id=exc.event_id,
                exception_type=exc.exc_data["type"],
                exception_msg=exc.exc_data["msg"],
                exception_info=exc.exc_data["info"],
                stack_info=exc.exc_data["stack"],
            )
            self.assertLessEqual(exp_data.items(), log_data.items())

    @patch("zq_django_util.logs.models.RequestLog.objects")
    def test__insert_into_database_request_log(
        self,
        mock_objects: MagicMock,
    ):
        request_items = baker.make(RequestLog, _quantity=10)

        handler = HandleLogAsync()
        handler._insert_into_database(request_items, [])

        mock_objects.using.assert_called_once_with("default")
        mock_objects.using().bulk_create.assert_called_once_with(request_items)

    @patch("zq_django_util.logs.models.RequestLog.objects")
    def test__insert_into_database_request_log_operational_error(
        self,
        mock_objects: MagicMock,
    ):
        mock_objects.using().bulk_create.side_effect = OperationalError()
        request_items = baker.make(RequestLog, _quantity=10)

        handler = HandleLogAsync()

        with self.assertRaises(Exception):
            handler._insert_into_database(request_items, [])

    @patch("loguru.logger")
    @patch("zq_django_util.logs.models.RequestLog.objects")
    def test__insert_into_database_request_log_other_error(
        self,
        mock_objects: MagicMock,
        mock_logger: MagicMock,
    ):
        mock_objects.using().bulk_create.side_effect = Exception("msg")

        request_items = []
        for i in range(10):
            request_items.append(baker.make(RequestLog))

        handler = HandleLogAsync()
        handler._insert_into_database(request_items, [])
        mock_logger.error.called_once_with("DRF API LOGGER EXCEPTION: msg")

    @patch.object(ExceptionLog, "save")
    def test__insert_into_database_exception_log(
        self,
        mock_save: MagicMock,
    ):
        exception_items = baker.prepare(ExceptionLog, _quantity=10)

        handler = HandleLogAsync()
        handler._insert_into_database([], exception_items)
        self.assertEqual(mock_save.call_count, 10)

    @patch("zq_django_util.logs.handler.HandleLogAsync._insert_into_database")
    @patch("zq_django_util.logs.handler.HandleLogAsync.prepare_request_log")
    def test__start_log_parse_request_log(
        self,
        mock_prepare_request_log: MagicMock,
        mock_insert_into_database: MagicMock,
    ):
        mock_prepare_request_log.return_value = {"ip": "123"}

        context = self.create_context()
        handler = HandleLogAsync()

        for i in range(10):
            handler.put_log_data(*context)

        handler._start_log_parse()
        self.assertEqual(mock_insert_into_database.call_count, 1)

    @patch("zq_django_util.logs.handler.HandleLogAsync._insert_into_database")
    @patch("zq_django_util.logs.handler.HandleLogAsync.prepare_exception_log")
    def test__start_log_parse_exception_log(
        self,
        mock_prepare_exception_log: MagicMock,
        mock_insert_into_database: MagicMock,
    ):
        mock_prepare_exception_log.return_value = {"ip": "123"}

        context = self.create_context(
            exception=ApiException(ResponseType.ServerError)
        )
        handler = HandleLogAsync()

        for i in range(10):
            handler.put_log_data(*context)

        handler._start_log_parse()
        self.assertEqual(mock_insert_into_database.call_count, 1)

    @patch("zq_django_util.logs.handler.HandleLogAsync._insert_into_database")
    @patch("zq_django_util.logs.handler.HandleLogAsync.prepare_exception_log")
    def test__start_log_parse_with_exception(
        self,
        mock_prepare_exception_log: MagicMock,
        mock_insert_into_database: MagicMock,
    ):
        mock_prepare_exception_log.side_effect = Exception("msg")

        context = self.create_context(
            exception=ApiException(ResponseType.ServerError)
        )
        handler = HandleLogAsync()

        for i in range(10):
            handler.put_log_data(*context)

        handler._start_log_parse()

        mock_insert_into_database.assert_not_called()
