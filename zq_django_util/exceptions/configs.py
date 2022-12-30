from typing import List, TypedDict

from django.core.signals import setting_changed
from django.dispatch import receiver

from zq_django_util.utils.package_settings import PackageSettings

ZqExceptionSettingDict = TypedDict(
    "ZqExceptionSettingDict",
    {
        "EXCEPTION_UNKNOWN_HANDLE": bool,
        "EXCEPTION_HANDLER_CLASS": str,
        "SENTRY_ENABLE": bool,
        "SENTRY_DSN": str,
    },
    total=True,
)


class ZqExceptionSettings(PackageSettings):
    setting_name = "ZQ_EXCEPTION"

    DEFAULTS: ZqExceptionSettingDict = {
        "EXCEPTION_UNKNOWN_HANDLE": True,  # 处理未知异常
        "EXCEPTION_HANDLER_CLASS": "zq_django_util.exceptions.handler.ApiExceptionHandler",
        "SENTRY_ENABLE": False,
        "SENTRY_DSN": "",
    }

    IMPORT_STRINGS: List[str] = ["EXCEPTION_HANDLER_CLASS"]


zq_exception_settings = ZqExceptionSettings()


@receiver(setting_changed)
def reload_settings(*args, **kwargs):
    zq_exception_settings.reload_package_settings(*args, **kwargs)
