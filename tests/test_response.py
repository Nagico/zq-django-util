import json

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase

from zq_django_util.exceptions import ApiException
from zq_django_util.response import ApiResponse, ResponseType
from zq_django_util.response.renderers import CustomRenderer


class ApiResponseTestCase(APITestCase):
    def test_response_with_api_exception(self):
        msg = "msg"

        exc = ApiException(ResponseType.ServerError, msg=msg)
        response = ApiResponse(ex=exc)
        self.assertEqual(response.status_code, exc.response_type.status_code)
        self.assertEqual(response.code, exc.response_type.code)
        self.assertEqual(response.detail, exc.response_type.detail)
        self.assertRegex(response.msg, f"^{msg}")
        self.assertEqual(response.data, "")

        self.assertRegex(
            str(response),
            f"^code: {exc.response_type.code}, detail: {exc.response_type.detail}",
        )


class ApiResponseRenderTestCase(APITestCase):
    def test_render_prepare_log_success(self):
        request = Request(APIRequestFactory().get("/test/"))
        response = self.client.get("/test/")

        render_response = CustomRenderer().render(
            data=response.data,
            accepted_media_type="application/json",
            renderer_context={"request": request, "response": response},
        )

        self.assertIs(response.api_request_data, request.data)

        render_data = json.loads(render_response.decode("utf-8"))

        self.assertEqual(render_data["code"], ResponseType.Success.code)
        self.assertEqual(render_data["detail"], ResponseType.Success.detail)
        self.assertEqual(render_data["msg"], ResponseType.Success.detail)
        self.assertDictEqual(render_data["data"], response.data)

    def test_render_prepare_log_fail(self):
        request = APIRequestFactory().get("/test/")
        response = self.client.get("/test/")

        CustomRenderer().render(
            data=response.data,
            accepted_media_type="application/json",
            renderer_context={"request": request, "response": response},
        )

        self.assertFalse(hasattr(response, "api_request_data"))
