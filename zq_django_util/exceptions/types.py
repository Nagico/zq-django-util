from datetime import datetime
from typing import Optional, TypedDict

from rest_framework.response import Response

from zq_django_util.exceptions import ApiException


class ExceptionInfo(TypedDict, total=True):
    type: str
    msg: str
    info: str
    stack: list[str]


class ExceptionData(TypedDict, total=False):
    eid: Optional[str]
    time: datetime
    exception: Optional[ExceptionInfo]


ExtraHeaders = TypedDict(
    "ExtraHeaders",
    {
        "WWW-Authenticate": str,
        "Retry-After": str,
    },
    total=False,
)


class ApiExceptionResponse(Response):
    exception_data: ApiException
