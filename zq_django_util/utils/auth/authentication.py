# 重写 jwt 相关验证类
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

from zq_django_util.exceptions import ApiException
from zq_django_util.response import ResponseType

AuthUser = get_user_model()


class OpenIdAuth(BaseBackend):
    """
    OpenID 验证模块(获取token时调用)
    """

    def authenticate(self, request, openid=None, **kwargs):
        """
        重写认证方法

        :param request: 传入请求

        :param openid: 传入openid

        :param kwargs: 字典参数

        :return: openid 对应用户对象
        """
        # 未传入openid 认证失败
        if openid is None:
            return
        # 获取 openid 对应用户
        try:
            user = AuthUser.objects.get(openid=openid)
        except AuthUser.DoesNotExist:
            # openid 无对应用户, 新增用户(is_active 为 true)
            user = AuthUser.objects.create(
                username=openid,
                openid=openid,
                is_active=True,
            )
            user.save()
        return user

    def get_user(self, user_id):
        """
        重写用户获取方法

        :param user_id: uid

        :return: 用户对象
        """
        try:
            user = AuthUser.objects.get(pk=user_id)
        except AuthUser.DoesNotExist:  # 用户不存在, 返回 None
            return None
        return user


class ActiveUserAuthentication(JWTAuthentication):
    """
    基础用户认证类
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_model = AuthUser

    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        # 获取用户 ID
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise ApiException(
                ResponseType.TokenInvalid, "token获取失败", record=True
            )  # token 不存在, 认证失败

        # 获取用户模型
        try:
            user = self.user_model.objects.get(
                **{api_settings.USER_ID_FIELD: user_id}
            )
        except self.user_model.DoesNotExist:
            raise ApiException(
                ResponseType.ResourceNotFound, "用户不存在", record=True
            )  # 用户不存在, 认证失败

        user = AuthUser.objects.get(pk=user_id)
        self.check_activate(user)  # 检查用户激活类型

        return user

    @staticmethod
    def check_activate(user: AuthUser):
        """
        检查是否激活
        """
        if not user.is_active:
            raise ApiException(
                ResponseType.NotActive,
                "您的账号未激活，请完善个人信息后重试"
            )


class NormalUserAuthentication(ActiveUserAuthentication):
    """
    无需激活的用户认证类
    """

    @staticmethod
    def check_activate(user):
        pass
