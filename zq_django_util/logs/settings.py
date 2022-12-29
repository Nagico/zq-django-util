from typing import List, TypedDict

from zq_django_util.utils.package_settings import PackageSettings

DrfLoggerSettingDict = TypedDict(
    "DrfLoggerSettingDict",
    {
        "DEFAULT_DATABASE": str,
        "QUEUE_MAX_SIZE": int,
        "INTERVAL": int,
        "DATABASE": bool,
        "SIGNAL": bool,
        "PATH_TYPE": str,
        "SKIP_URL_NAME": List[str],
        "SKIP_NAMESPACE": List[str],
        "METHODS": List[str],
        "STATUS_CODES": List[int],
        "SENSITIVE_KEYS": List[str],
    },
    total=True,
)


class DrfLoggerSettings(PackageSettings):
    setting_name = "DRF_LOGGER"

    DEFAULTS: DrfLoggerSettingDict = {
        "DEFAULT_DATABASE": "default",
        "QUEUE_MAX_SIZE": 50,
        "INTERVAL": 10,
        "DATABASE": False,
        "SIGNAL": False,
        "PATH_TYPE": "FULL_PATH",
        "SKIP_URL_NAME": [""],
        "SKIP_NAMESPACE": [],
        "METHODS": None,
        "STATUS_CODES": [],
        "SENSITIVE_KEYS": ["password", "token", "access", "refresh"],
    }

    IMPORT_STRINGS: List[str] = []


drf_logger_settings = DrfLoggerSettings()
