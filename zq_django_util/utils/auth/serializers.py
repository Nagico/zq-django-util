from typing import Any, Dict

import rest_framework_simplejwt.settings
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    PasswordField,
    TokenObtainPairSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

from zq_django_util.exceptions import ApiException
from zq_django_util.response import ResponseType
from zq_django_util.utils.auth.backends import OpenIdBackend
from zq_django_util.utils.auth.exceptions import OpenIdNotBound
from zq_django_util.utils.auth.types import TokenVO

AuthUser = get_user_model()


class OpenIdLoginSerializer(serializers.Serializer):
    """
    OpenID Token 获取序列化器
    """

    openid_field = getattr(settings, "OPENID_FIELD", "openid")

    openid = PasswordField()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @classmethod
    def get_token(cls, user: AuthUser) -> RefreshToken:
        """
        获取 token(access与refresh)

        :param user: user对象

        :return: token 对象
        """
        # 调用 simple-jwt 中 token 生成方法, 需要在 settings 中指定 USER_ID_FIELD 为主键名
        return RefreshToken.for_user(user)

    def validate(self, attrs: Dict[str, Any]) -> TokenVO:
        """
        重写验证器

        :param attrs: 序列化器中待验证的数据

        :return: 已验证数据，返回前端
        """
        openid = self.get_open_id(attrs)
        # 验证 openid
        authenticate_kwargs = {"openid": openid}  # 给 openid 验证模块准备 openid
        try:
            #  给 openid 验证模块准备请求数据
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass

        openid_backend = OpenIdBackend()  # 实例化 openid 验证模块

        try:
            user: AuthUser = openid_backend.authenticate(
                **authenticate_kwargs, raise_exception=True
            )  # 调用 openid 验证模块进行权限验证
        except OpenIdNotBound:  # openid 未绑定用户
            user = self.handle_new_openid(openid)  # 处理新 openid

        # token 获取
        user_id_field = (
            rest_framework_simplejwt.settings.api_settings.USER_ID_FIELD
        )  # 读取 settings 中定义的 user 主键字段名
        data: TokenVO = {}  # 待返回数据
        refresh = self.get_token(user)  # 获取 token
        data["id"] = getattr(user, user_id_field)  # 返回用户id
        data["access"] = str(refresh.access_token)  # 返回 access token
        data["refresh"] = str(refresh)  # 返回 refresh token
        data["username"] = user.username  # 返回用户名

        return data

    def get_open_id(self, attrs: Dict[str, Any]) -> str:
        """
        获取 openid
        """
        return attrs[self.openid_field]

    def handle_new_openid(self, openid: str) -> AuthUser:
        """
        处理新 openid
        如果自动注册需要返回对象
        """
        raise ApiException(
            ResponseType.ThirdLoginFailed,
            msg="该微信账号暂未未绑定用户",
            detail="openid未绑定",
        )


class AbstractWechatLoginSerializer(OpenIdLoginSerializer):
    """
    微信登录序列化器
    """

    code = PasswordField(label="前端获取code")  # 前端传入 code

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields.pop("openid")  # 删除 openid 字段

    def get_open_id(self, attrs: Dict[str, Any]) -> str:
        """
        重写获取 open_id 方法
        """
        raise NotImplementedError("请在此返回openid")


class PasswordLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs: Dict[str, Any]) -> TokenVO:
        data: TokenVO = super().validate(attrs)
        user_id_field = (
            rest_framework_simplejwt.settings.api_settings.USER_ID_FIELD
        )  # 读取 settings 中定义的 user 主键字段名
        data["id"] = getattr(self.user, user_id_field)  # 返回用户id
        data["username"] = self.user.username  # 返回用户名
        return data
