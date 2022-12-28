from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

from zq_django_util.exceptions import ApiException
from zq_django_util.response import ResponseType
from zq_django_util.utils.auth.serializers import (
    OpenIDLoginSerializer,
    PasswordLoginSerializer,
    WechatLoginSerializer,
)

AuthUser = get_user_model()


class OpenIDLoginView(TokenObtainPairView):
    """
    open id 登录视图（仅供测试微信登录使用）
    """

    queryset = AuthUser.objects.all()
    serializer_class = OpenIDLoginSerializer

    def post(self, request, *args, **kwargs):
        """
        增加 post 方法, 支持 open id 登录
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            raise ApiException(ResponseType.ThirdLoginFailed, "微信登录失败，请稍后重试")

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class WechatLoginView(OpenIDLoginView):
    """
    微信登录视图
    """

    queryset = AuthUser.objects.all()
    serializer_class = WechatLoginSerializer


class PasswordLoginView(TokenObtainPairView):
    """
    密码登录视图
    """

    serializer_class = PasswordLoginSerializer
