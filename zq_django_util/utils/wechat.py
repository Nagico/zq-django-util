from django.conf import settings
from django.core.cache import caches
from wechatpy import WeChatClientException
from wechatpy.client import WeChatClient
from wechatpy.session import SessionStorage

from zq_django_util.exceptions import ApiException
from zq_django_util.response import ResponseType


class WechatCache(SessionStorage):
    def __init__(self, cache):
        self.cache = cache

    def get(self, key, default=None):
        return self.cache.get(key, default)

    def set(self, key, value, ttl=None):
        self.cache.set(key, value, timeout=ttl)

    def delete(self, key):
        self.cache.delete(key)


wechat_client = WeChatClient(
    settings.APPID,
    settings.SECRET,
    session=WechatCache(caches["wechat_session"]),
)


ENV_VERSION = "release"
if settings.SERVER_URL in settings.RELEASE_SERVER:
    ENV_VERSION = "release"
elif settings.SERVER_URL in settings.TEST_SERVER:
    ENV_VERSION = "trial"


def get_openid(code: str) -> dict:
    """
    获取小程序登录后 openid
    :param code: 临时 code
    :return: openid
    """
    try:
        return wechat_client.wxa.code_to_session(code)
    except WeChatClientException as e:
        if e.errcode == 40029:
            raise ApiException(
                ResponseType.ThirdLoginExpired, "微信登录失败，请重新登录"
            )
        raise ApiException(
            ResponseType.ThirdLoginFailed,
            f"微信登录失败 [{e.errcode}] {e.errmsg}",
            record=True,
        )


def get_user_phone_num(code: str) -> str:
    """
    获取用户手机号
    :param code: 临时 code
    :return: 手机号
    """
    try:
        result = wechat_client.wxa.getuserphonenumber(code)

        if result["phone_info"]["countryCode"] != "86":
            raise ApiException(
                ResponseType.ParamValidationFailed,
                f"仅支持中国大陆手机号"
            )

        return result["phone_info"]["purePhoneNumber"]
    except WeChatClientException as e:
        raise ApiException(
            ResponseType.ThirdLoginFailed,
            f"[{e.errcode}] {e.errmsg}"
        )
