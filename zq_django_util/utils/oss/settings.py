from typing import List, TypedDict

from zq_django_util.utils.package_settings import PackageSettings

OssSettingDict = TypedDict(
    "OssSettingDict",
    {
        "ACCESS_KEY_ID": str,
        "ACCESS_KEY_SECRET": str,
        "END_POINT": str,
        "BUCKET_NAME": str,
        "URL_EXPIRE_SECOND": int,
        "TOKEN_EXPIRE_SECOND": int,
        "MAX_SIZE_MB": int,
    },
)


class OssSettings(PackageSettings):
    setting_name = "ALIYUN_OSS"

    DEFAULTS: OssSettingDict = {
        "ACCESS_KEY_ID": "",
        "ACCESS_KEY_SECRET": "",
        "ENDPOINT": "",
        "BUCKET_NAME": "",
        "URL_EXPIRE_SECOND": 60 * 60 * 24 * 30,
        "TOKEN_EXPIRE_SECOND": 60,
        "MAX_SIZE_MB": 100,
    }

    IMPORT_STRINGS: List[str] = []


oss_settings = OssSettings()
