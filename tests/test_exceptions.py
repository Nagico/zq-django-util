import json
from typing import Any, Optional
from unittest.mock import MagicMock, call, patch

import django.core.exceptions as django_exceptions
import rest_framework.exceptions as drf_exceptions
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import TestCase, override_settings
from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ExceptionHandlerContext
from rest_framework import status
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.viewsets import GenericViewSet

from zq_django_util.exceptions import ApiException
from zq_django_util.exceptions.handler import (
    ApiExceptionHandler,
    exception_handler,
)
from zq_django_util.exceptions.types import ApiExceptionResponse
from zq_django_util.exceptions.views import server_error
from zq_django_util.response import ApiResponse, ResponseType


class ApiExceptionTestCase(TestCase):
    EID_REX = r"[0-9a-z]{6}"

    def test_gen_exp_id(self):
        eid = ApiException.get_exp_id()
        self.assertRegex(eid, f"^{self.EID_REX}$")

    def test_get_exp_info(self):
        msg = "msg"
        try:
            raise ValueError(msg)
        except ValueError:
            info = ApiException.get_exception_info()
            self.assertEqual(info["type"], "<class 'ValueError'>")
            self.assertEqual(info["msg"], msg)
            self.assertRegex(
                info["info"], r"    raise ValueError\(msg\)\nValueError: msg$"
            )
            self.assertRegex(
                info["stack"][-1], r'"stack": traceback.format_stack()'
            )

    @override_settings(DEBUG=True)
    def test_exception_data_debug(self):
        data = {"a": 1}

        exc = ApiException(ResponseType.ServerError)
        exc.exc_data = data

        res = exc.exception_data

        self.assertEqual(res["eid"], exc.eid)
        self.assertEqual(res["time"], exc.time)
        self.assertDictEqual(res["exception"], data)

    @override_settings(DEBUG=False)
    def test_exception_data_not_debug(self):
        data = {"a": 1}

        exc = ApiException(ResponseType.ServerError)
        exc.exc_data = data

        res = exc.exception_data

        self.assertEqual(res["eid"], exc.eid)
        self.assertEqual(res["time"], exc.time)
        self.assertNotIn("exception", res)

    def test_inner_exception(self):
        inner = ValueError("inner msg")
        exc = ApiException(ResponseType.ServerError, inner=inner)
        self.assertEqual(exc.inner, inner)

    # region response type
    def test_response_type_not_record_default(self):
        exc = ApiException(ResponseType.NotLogin)
        self.assertEqual(exc.response_type, ResponseType.NotLogin)
        self.assertFalse(exc.record)

    def test_response_type_not_record_force(self):
        exc = ApiException(ResponseType.ServerError, record=False)
        self.assertEqual(exc.response_type, ResponseType.ServerError)
        self.assertFalse(exc.record)

    def test_response_type_record_default(self):
        exc = ApiException(ResponseType.ServerError)
        self.assertEqual(exc.response_type, ResponseType.ServerError)
        self.assertTrue(exc.record)

    def test_response_type_record_force(self):
        exc = ApiException(ResponseType.NotLogin, record=True)
        self.assertEqual(exc.response_type, ResponseType.NotLogin)
        self.assertTrue(exc.record)

    # endregion

    # region msg
    def test_msg_not_record_default(self):
        exc = ApiException(ResponseType.NotLogin)
        self.assertEqual(exc.msg, ResponseType.NotLogin.detail)

    def test_msg_not_record_custom(self):
        msg = "custom"

        exc = ApiException(ResponseType.NotLogin, msg=msg)
        self.assertEqual(exc.msg, msg)

    def test_msg_record_default(self):
        exc = ApiException(ResponseType.ServerError)
        self.assertRegex(
            exc.msg,
            f"^{ApiException.DEFAULT_MSG}，{ApiException.RECORD_MSG_TEMPLATE}{self.EID_REX}$",
        )

    def test_msg_record_custom(self):
        msg = "custom"

        exc = ApiException(ResponseType.ServerError, msg=msg)
        self.assertRegex(
            exc.msg,
            f"^{msg}，{ApiException.RECORD_MSG_TEMPLATE}{self.EID_REX}$",
        )

    # endregion

    # region detail
    def test_detail_not_record_default(self):
        exc = ApiException(ResponseType.NotLogin)
        self.assertEqual(exc.detail, ResponseType.NotLogin.detail)

    def test_detail_not_record_custom(self):
        detail = "custom"

        exc = ApiException(ResponseType.NotLogin, detail=detail)
        self.assertEqual(exc.detail, detail)

    def test_detail_record_default(self):
        exc = ApiException(ResponseType.ServerError)
        self.assertRegex(
            exc.detail, f"^{ResponseType.ServerError.detail}, {self.EID_REX}$"
        )

    def test_detail_record_custom(self):
        detail = "custom"

        exc = ApiException(ResponseType.ServerError, detail=detail)
        self.assertRegex(exc.detail, f"^{detail}, {self.EID_REX}$")

    # endregion

    def test_response_data(self):
        try:
            inner = ValueError("inner msg")
            raise ApiException(
                ResponseType.LoginFailed,
                msg="msg",
                detail="detail",
                inner=inner,
                record=True,
            )
        except ApiException as e:
            response = e.response_data
            self.assertEqual(response["code"], ResponseType.LoginFailed.code)
            self.assertEqual(response["msg"], e.msg)
            self.assertEqual(response["detail"], e.detail)
            self.assertDictEqual(response["data"], e.exception_data)


class TestExceptionHandler(ApiExceptionHandler):
    def run(self) -> Optional[ApiExceptionResponse]:
        return None


class TestExceptHandlerBlank:
    pass


class ExceptionHandlerTestCase(TestCase):
    class TestViewSet(ListModelMixin, GenericViewSet):
        def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
            return Response({})

    @property
    def context(self) -> ExceptionHandlerContext:
        request = APIRequestFactory().request()
        return dict(
            view=self.TestViewSet(),
            args=tuple(),
            kwargs=dict(),
            request=request,
        )

    @override_settings(ZQ_EXCEPTION={}, DEBUG=True)
    def test_exception_handler_default(self):
        try:
            raise ApiException(ResponseType.ServerError)
        except ApiException as e:
            response = exception_handler(e, self.context)
            with patch(
                "zq_django_util.exceptions.ApiException.get_exp_id",
                return_value=response.data["data"]["eid"],
            ):
                standard_response_data = ApiException(
                    ResponseType.ServerError
                ).response_data

                handler_response_data = response.exception_data.response_data
                self.assertIsNotNone(response)
                self.assertEqual(
                    response.status_code, ResponseType.ServerError.status_code
                )

                self.assertIn("exception", handler_response_data["data"])
                self.assertIn("exception", standard_response_data["data"])
                handler_response_data["data"]["exception"] = None
                standard_response_data["data"]["exception"] = None

                self.assertIn("time", handler_response_data["data"])
                self.assertIn("time", standard_response_data["data"])
                standard_response_data["data"]["time"] = handler_response_data[
                    "data"
                ]["time"]

                self.assertDictEqual(
                    handler_response_data, standard_response_data
                )

    @override_settings(
        ZQ_EXCEPTION={
            "EXCEPTION_HANDLER_CLASS": "tests.test_exceptions.TestExceptionHandler"
        }
    )
    def test_exception_handler_custom(self):
        try:
            raise ApiException(ResponseType.ServerError)
        except ApiException as e:
            response = exception_handler(e, self.context)
            self.assertIsNone(response)

    @override_settings(
        ZQ_EXCEPTION={
            "EXCEPTION_HANDLER_CLASS": "tests.test_exceptions.TestExceptHandlerBlank"
        }
    )
    def test_exception_handler_custom_class_type_error(self):
        try:
            raise ApiException(ResponseType.ServerError)
        except ApiException as e:
            with self.assertRaises(ImportError) as cm:
                exception_handler(e, self.context)
            self.assertRegex(
                cm.exception.args[0],
                r"is not a subclass of ApiExceptionHandler$",
            )


class ApiExceptionHandlerTestCase(TestCase):
    class TestViewSet(ListModelMixin, GenericViewSet):
        def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
            return Response({})

    @property
    def context(self) -> ExceptionHandlerContext:
        request = APIRequestFactory().request()

        return dict(
            view=self.TestViewSet(),
            args=tuple(),
            kwargs=dict(),
            request=request,
        )

    def test_convert_unhandled_exceptions_convert(self):
        msg = "msg"
        exc = ValueError(msg)
        api_exc = ApiExceptionHandler.convert_unhandled_exceptions(exc)
        self.assertIsInstance(api_exc, drf_exceptions.APIException)
        self.assertEqual(api_exc.detail, msg)
        self.assertEqual(
            api_exc.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def test_convert_unhandled_exceptions_not_convert(self):
        msg = "msg"
        exc = drf_exceptions.NotFound(detail=msg)
        api_exc = ApiExceptionHandler.convert_unhandled_exceptions(exc)
        self.assertIs(api_exc, exc)

        exc = ApiException(ResponseType.ServerError, msg=msg)
        api_exc = ApiExceptionHandler.convert_unhandled_exceptions(exc)
        self.assertIs(api_exc, exc)

    def test_convert_drf_exceptions_convert_unknown(self):
        class UnknownDrfException(drf_exceptions.APIException):
            status_code = 999

        exc = UnknownDrfException()
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertTrue(api_exc.record)
        self.assertEqual(api_exc.response_type, ResponseType.ServerError)

    def test_convert_drf_exceptions_convert_parser_error(self):
        exc = drf_exceptions.ParseError()
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertFalse(api_exc.record)
        self.assertEqual(api_exc.response_type, ResponseType.JSONParseFailed)

    def test_convert_drf_exceptions_convert_authentication_failed(self):
        exc = drf_exceptions.AuthenticationFailed()
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertFalse(api_exc.record)
        self.assertEqual(api_exc.response_type, ResponseType.LoginFailed)

    def test_convert_drf_exceptions_convert_not_authenticated(self):
        exc = drf_exceptions.NotAuthenticated()
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertFalse(api_exc.record)
        self.assertEqual(api_exc.response_type, ResponseType.NotLogin)

    def test_convert_drf_exceptions_convert_permission_denied(self):
        exc = drf_exceptions.PermissionDenied()
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertFalse(api_exc.record)
        self.assertEqual(api_exc.response_type, ResponseType.PermissionDenied)

    def test_convert_drf_exceptions_convert_not_found(self):
        exc = drf_exceptions.NotFound()
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertFalse(api_exc.record)
        self.assertEqual(api_exc.response_type, ResponseType.APINotFound)

    def test_convert_drf_exceptions_convert_validation_error(self):
        exc = drf_exceptions.ValidationError()
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertTrue(api_exc.record)
        self.assertEqual(
            api_exc.response_type, ResponseType.ParamValidationFailed
        )

    def test_convert_drf_exceptions_convert_method_not_allowed(self):
        exc = drf_exceptions.MethodNotAllowed("POST")
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertTrue(api_exc.record)
        self.assertEqual(api_exc.response_type, ResponseType.MethodNotAllowed)
        self.assertRegex(api_exc.detail, "^不允许POST请求")

    def test_convert_drf_exceptions_convert_not_acceptable(self):
        exc = drf_exceptions.NotAcceptable("application/json")
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertTrue(api_exc.record)
        self.assertEqual(
            api_exc.response_type, ResponseType.HeaderNotAcceptable
        )
        self.assertRegex(api_exc.detail, "^不支持application/json的响应格式")

    def test_convert_drf_exceptions_convert_unsupported_media_type(self):
        exc = drf_exceptions.UnsupportedMediaType("zip")
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertTrue(api_exc.record)
        self.assertEqual(
            api_exc.response_type, ResponseType.UnsupportedMediaType
        )
        self.assertRegex(api_exc.detail, "^不支持zip的请求格式")
        self.assertRegex(api_exc.msg, "^暂不支持zip文件上传，请使用支持的文件格式重试")

    def test_convert_drf_exceptions_convert_throttled(self):
        exc = drf_exceptions.Throttled(20)
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIsInstance(api_exc, ApiException)
        self.assertIs(api_exc.inner, exc)
        self.assertTrue(api_exc.record)
        self.assertEqual(api_exc.response_type, ResponseType.APIThrottled)
        self.assertRegex(api_exc.detail, "^请求频率过高，请20s后再试")
        self.assertRegex(api_exc.msg, "^请求太快了，请20s后再试")

    def test_convert_drf_exceptions_not_convert(self):
        exc = ApiException(ResponseType.ServerError)
        api_exc = ApiExceptionHandler.convert_drf_exceptions(exc)
        self.assertIs(api_exc, exc)

    def test_convert_known_exceptions_convert_http_404(self):
        exc = Http404()
        drf_exc = ApiExceptionHandler.convert_known_exceptions(exc)
        self.assertIsInstance(drf_exc, drf_exceptions.NotFound)

    def test_convert_known_exceptions_convert_permission_denied(self):
        exc = django_exceptions.PermissionDenied()
        drf_exc = ApiExceptionHandler.convert_known_exceptions(exc)
        self.assertIsInstance(drf_exc, drf_exceptions.PermissionDenied)

    def test_convert_known_exceptions_not_convert(self):
        exc = ValueError()
        same_exc = ApiExceptionHandler.convert_known_exceptions(exc)
        self.assertIs(same_exc, exc)

    def test_get_headers_auth_header(self):
        exc = Exception()
        exc.auth_header = "Basic"
        headers = ApiExceptionHandler.get_headers(exc)
        self.assertDictEqual(headers, {"WWW-Authenticate": "Basic"})

    def test_get_headers_wait(self):
        exc = drf_exceptions.Throttled(20)
        headers = ApiExceptionHandler.get_headers(exc)
        self.assertDictEqual(headers, {"Retry-After": "20"})

    @override_settings(DEBUG=False)
    def test_get_response_without_inner(self):
        try:
            raise ApiException(ResponseType.ServerError)
        except ApiException as exc:
            response = ApiExceptionHandler(exc, self.context).get_response(exc)
            self.assertEqual(
                response.status_code, exc.response_type.status_code
            )
            self.assertEqual(response.content_type, "application/json")

            response_data = exc.response_data
            response_data["data"]["details"] = None
            self.assertDictEqual(response.data, response_data)

    def test_get_response_with_drf_exception_inner(self):
        try:
            raise ApiException(
                ResponseType.ServerError, inner=drf_exceptions.NotFound()
            )
        except ApiException as exc:
            response = ApiExceptionHandler(exc, self.context).get_response(exc)
            info = ExceptionFormatter(exc.inner, self.context, exc).run()

            self.assertDictEqual(response.data["data"]["details"], info)

    def test_get_response_with_exception_msg_inner(self):
        msg = "msg"
        try:
            raise ApiException(ResponseType.ServerError, inner=ValueError(msg))
        except ApiException as exc:
            response = ApiExceptionHandler(exc, self.context).get_response(exc)

            self.assertEqual(response.data["data"]["details"], msg)

    def test_get_response_with_exception_not_msg_inner(self):
        try:
            raise ApiException(ResponseType.ServerError, inner=ValueError())
        except ApiException as exc:
            response = ApiExceptionHandler(exc, self.context).get_response(exc)

            self.assertIsNone(response.data["data"]["details"])


class ApiExceptionHandlerSentryTestCase(TestCase):

    User = get_user_model()

    class TestViewSet(ListModelMixin, GenericViewSet):
        def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
            return Response({})

    def context(self, user: Optional[User] = None) -> ExceptionHandlerContext:
        request = APIRequestFactory().request()
        if user:
            request.user = user
        else:
            request.user = AnonymousUser()

        return dict(
            view=self.TestViewSet(),
            args=tuple(),
            kwargs=dict(),
            request=request,
        )

    @patch("sentry_sdk.api.set_tag")
    @patch("sentry_sdk.set_context")
    @patch("sentry_sdk.api.capture_exception", return_value="event_id")
    @patch(
        "zq_django_util.exceptions.handler.ApiExceptionHandler.notify_sentry"
    )
    def test__notify_sentry(
        self,
        mock_notify_sentry: MagicMock,
        mock_capture_exception: MagicMock,
        mock_set_context: MagicMock,
        mock_set_tag: MagicMock,
    ):
        try:
            raise ApiException(ResponseType.ServerError)
        except ApiException as exc:
            handler = ApiExceptionHandler(exc, self.context())
            response = handler.get_response(exc)

            handler._notify_sentry(exc, response)

            mock_notify_sentry.assert_called_once_with(exc, response)
            mock_set_tag.assert_called_once_with(
                "exception_type", exc.response_type.name
            )
            mock_set_context.assert_has_calls(
                calls=[
                    call(
                        "exp_info",
                        {
                            "eid": response.data["data"]["eid"],
                            "code": response.data["code"],
                            "detail": response.data["detail"],
                            "msg": response.data["msg"],
                        },
                    ),
                    call("details", response.data["data"]["details"]),
                ]
            )
            mock_capture_exception.assert_called_once_with(exc)

    @patch("sentry_sdk.api.set_tag")
    @patch("sentry_sdk.set_context")
    @patch("sentry_sdk.api.capture_exception", return_value="event_id")
    @patch(
        "zq_django_util.exceptions.handler.ApiExceptionHandler.notify_sentry",
        side_effect=Exception,
    )
    def test__notify_sentry_exception(
        self,
        mock_notify_sentry: MagicMock,
        mock_capture_exception: MagicMock,
        mock_set_context: MagicMock,
        mock_set_tag: MagicMock,
    ):
        try:
            raise ApiException(ResponseType.ServerError)
        except ApiException as exc:
            handler = ApiExceptionHandler(exc, self.context())
            response = handler.get_response(exc)

            handler._notify_sentry(exc, response)

            mock_set_tag.assert_called_once()
            mock_notify_sentry.assert_called()

    @patch("sentry_sdk.api.set_tag")
    @patch("sentry_sdk.api.set_user")
    def test_notify_sentry_anonymous(
        self,
        mock_set_user: MagicMock,
        mock_set_tag: MagicMock,
    ):
        try:
            raise ApiException(ResponseType.ServerError)
        except ApiException as exc:
            handler = ApiExceptionHandler(exc, self.context())
            response = handler.get_response(exc)

            handler.notify_sentry(exc, response)

            mock_set_tag.assert_called_once_with("role", "guest")
            mock_set_user.assert_not_called()

    @patch("sentry_sdk.api.set_tag")
    @patch("sentry_sdk.api.set_user")
    def test_notify_sentry_user(
        self,
        mock_set_user: MagicMock,
        mock_set_tag: MagicMock,
    ):
        user = self.User.objects.create(username="test")
        try:
            raise ApiException(ResponseType.ServerError)
        except ApiException as exc:
            handler = ApiExceptionHandler(exc, self.context(user))
            response = handler.get_response(exc)

            handler.notify_sentry(exc, response)

            mock_set_tag.assert_called_once_with("role", "user")
            mock_set_user.assert_called_once_with(
                {"email": "test", "id": 1, "phone": None}
            )

    @override_settings(
        ZQ_EXCEPTION={
            "SENTRY_ENABLE": True,
        }
    )
    @patch("sentry_sdk.api.set_tag")
    @patch("sentry_sdk.set_context")
    @patch("sentry_sdk.api.capture_exception", return_value="event_id")
    @patch(
        "zq_django_util.exceptions.handler.ApiExceptionHandler.notify_sentry"
    )
    def test_run_with_sentry(
        self,
        mock_notify_sentry: MagicMock,
        mock_capture_exception: MagicMock,
        mock_set_context: MagicMock,
        mock_set_tag: MagicMock,
    ):
        try:
            raise ApiException(ResponseType.ServerError)
        except ApiException as exc:
            handler = ApiExceptionHandler(exc, self.context())
            response = handler.run()

            mock_notify_sentry.assert_called_once_with(exc, response)
            mock_capture_exception.assert_called_once_with(exc)
            self.assertEqual(response.data["data"]["event_id"], "event_id")


class ExceptionViewTestCase(APITestCase):
    def test_404(self):
        response = self.client.get("/./")
        self.assertEqual(response.status_code, 404)

        response = response.json()
        self.assertDictEqual(
            response,
            ApiResponse(ResponseType.APINotFound, "您访问的页面不存在").__dict__(),
        )

    def test_500(self):
        response = server_error(APIRequestFactory().request())

        self.assertEqual(response.status_code, 500)

        response = json.loads(response.content)
        self.assertDictEqual(
            response, ApiResponse(ResponseType.ServerError).__dict__()
        )
