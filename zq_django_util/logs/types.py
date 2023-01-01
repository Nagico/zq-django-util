from datetime import datetime
from typing import TypedDict, Union

from zq_django_util.response.types import JSONVal

HeaderContent = Union[str, list["HeaderContent"], dict[str, "HeaderContent"]]
HeaderDict = dict[str, HeaderContent]


class FileDataDict(TypedDict, total=True):
    name: str
    size: int
    content_type: str
    content_type_extra: str


class RequestLogDict(TypedDict, total=True):
    user: int | None
    ip: str
    method: str
    url: str
    headers: HeaderDict
    content_type: str
    query_param: dict[str, JSONVal]
    request_body: dict[str, JSONVal]
    file_data: dict[str, FileDataDict]
    response: JSONVal
    status_code: int
    execution_time: float | None
    create_time: datetime


class ExceptionLogDict(RequestLogDict, total=True):
    exp_id: str | None
    event_id: str | None
    exception_type: str
    exception_msg: str
    exception_info: str
    stack_info: list[str]
