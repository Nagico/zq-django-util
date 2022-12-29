from django.http import HttpRequest, JsonResponse

from zq_django_util.response import ApiResponse, ResponseType


def bad_request(request: HttpRequest, exception: Exception) -> JsonResponse:
    """
    404 页面

    在 url.py 中设定 handler404 为此函数

    """
    return ApiResponse(ResponseType.NOT_FOUND, "您访问的页面不存在").to_json_response()


def server_error(request: HttpRequest) -> JsonResponse:
    """
    500 页面

    在 url.py 中设定 handler500 为此函数

    """
    return ApiResponse(ResponseType.ServerError).to_json_response()
