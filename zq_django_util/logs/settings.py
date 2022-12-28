from typing import Dict, List, Union

from zq_django_util.utils.package_settings import PackageSettings


class DrfLoggerSettings(PackageSettings):
    setting_name = "DRF_LOGGER"

    DEFAULTS: Dict[str, Union[str, int, bool, list[str]]] = {
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


drf_logger_settings = DrfLoggerSettings()  # type: ignore
