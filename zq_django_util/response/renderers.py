# 自定义返回格式
from rest_framework.renderers import JSONRenderer

from zq_django_util.response import ApiResponse


class CustomRenderer(JSONRenderer):
    # 重构render方法
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context["response"]
        if renderer_context:
            try:  # 记录请求数据，便于日志处理
                request_data = renderer_context["request"].data
                response.api_request_data = request_data
            except Exception:
                pass

            if not response.exception:  # 如果不是异常
                data = ApiResponse(data=data).__dict__()  # 将data包装成ApiResponse

        return super().render(data, accepted_media_type, renderer_context)
