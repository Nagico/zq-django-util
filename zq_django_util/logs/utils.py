import re
from typing import Union

from zq_django_util.logs.settings import drf_logger_settings


def get_headers(request=None):
    """
    Function:       get_headers(self, request)
    Description:    To get all the headers from request
    """
    regex = re.compile("^HTTP_")
    return dict(
        (regex.sub("", header), value)
        for (header, value) in request.META.items()
        if header.startswith("HTTP_")
    )


def get_client_ip(request):
    try:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
    except:
        return ""


def is_api_logger_enabled():
    return drf_logger_settings.DATABASE or drf_logger_settings.SIGNAL


def database_log_enabled():
    return drf_logger_settings.DATABASE


def mask_sensitive_data(data: Union[dict, list, str]) -> Union[dict, list, str]:  # type: ignore
    """
    Hides sensitive keys specified in sensitive_keys settings.
    Loops recursively over nested dictionaries.
    """

    if type(data) != dict:
        return data

    for key, value in data.items():
        if key in drf_logger_settings.SENSITIVE_KEYS:
            length = len(data[key])
            data[key] = f"***FILTERED*** (len: {length})"

        if type(value) == dict:
            data[key] = mask_sensitive_data(data[key])

        if type(value) == list:
            data[key] = [mask_sensitive_data(item) for item in data[key]]

    return data
