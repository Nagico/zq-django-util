import base64
import json
import time
from queue import Queue
from threading import Thread
from typing import Optional

from django.core.files.uploadedfile import UploadedFile
from django.db.utils import OperationalError
from django.urls import resolve
from django.utils import timezone
from logs import API_LOGGER_SIGNAL  # type: ignore
from loguru import logger
from rest_framework.request import Request
from rest_framework.response import Response

from zq_django_util.exceptions import ApiException
from zq_django_util.logs.models import ExceptionLog, RequestLog
from zq_django_util.logs.settings import drf_logger_settings
from zq_django_util.logs.utils import (
    get_client_ip,
    get_headers,
    mask_sensitive_data,
)


class HandleLogAsync(Thread):
    def __init__(self):
        super().__init__()
        self._queue: Queue[(Request, Response, int)] = Queue(
            maxsize=drf_logger_settings.QUEUE_MAX_SIZE
        )

    def run(self) -> None:
        self.start_queue_process()

    def prepare_request_log(
        self, request: Request, response: Response, start_time: int
    ) -> Optional[dict]:
        # region 检查是否需要记录日志
        if not drf_logger_settings.DATABASE and not drf_logger_settings.SIGNAL:
            return

        url_name = resolve(request.path_info).url_name
        namespace = resolve(request.path_info).namespace

        # Always skip Admin panel
        if (
            namespace == "admin"
            or namespace == "__debug__"
            or url_name in drf_logger_settings.SKIP_URL_NAME
            or namespace in drf_logger_settings.SKIP_NAMESPACE
        ):
            return

        # Only log required status codes if matching
        if (
            drf_logger_settings.STATUS_CODES
            and response.status_code not in drf_logger_settings.STATUS_CODES
        ):
            return

        # Log only registered methods if available.
        if (
            drf_logger_settings.METHODS is not None
            and request.method not in drf_logger_settings.METHODS
        ):
            return

        # endregion
        data = self.get_request_log_data(request, response, start_time)

        if drf_logger_settings.SIGNAL:
            API_LOGGER_SIGNAL.listen(**data)

        if drf_logger_settings.DATABASE:
            return data

    def put_log_data(
        self, request: Request, response: Response, start_time: int
    ) -> None:
        self._queue.put((request, response, start_time))

        if self._queue.qsize() >= drf_logger_settings.QUEUE_MAX_SIZE:
            self._start_log_parse()

    def start_queue_process(self):
        while True:
            time.sleep(drf_logger_settings.INTERVAL)
            self._start_log_parse()

    def _start_log_parse(self) -> None:
        request_items: list[RequestLog] = []
        exception_items: list[ExceptionLog] = []
        while not self._queue.empty():
            try:
                request, response, start_time = self._queue.get()

                if getattr(response, "exception_data", False):
                    res = self.prepare_exception_log(
                        request, response, start_time
                    )
                    if res:
                        exception_items.append(ExceptionLog(**res))
                else:
                    res = self.prepare_request_log(
                        request, response, start_time
                    )
                    if res:
                        request_items.append(RequestLog(**res))
            except:
                pass

        if request_items or exception_items:
            self._insert_into_data_base(request_items, exception_items)

    def _insert_into_data_base(
        self,
        request_items: list[RequestLog],
        exception_items: list[ExceptionLog],
    ) -> None:
        try:
            if request_items:
                RequestLog.objects.using(
                    drf_logger_settings.DEFAULT_DATABASE
                ).bulk_create(request_items)
                logger.debug(
                    f"insert {len(request_items)} request log into database"
                )
            if (
                exception_items
            ):  # TODO 无法直接使用bulk_create: Can't bulk create a multi-table inherited model
                for item in exception_items:
                    item.save()
                logger.debug(
                    f"insert {len(exception_items)} exception log into database"
                )
        except OperationalError:
            raise Exception(
                """
            DRF API LOGGER EXCEPTION
            Model does not exists.
            Did you forget to migrate?
            """
            )
        except Exception as e:
            logger.error(f"DRF API LOGGER EXCEPTION: {e}")

    def prepare_exception_log(
        self, request: Request, response: Response, start_time: int
    ) -> dict:
        data = self.get_request_log_data(request, response, start_time)
        exception_data: ApiException = response.exception_data
        data.update(
            dict(
                exp_id=exception_data.eid,
                event_id=exception_data.event_id,
                exception_type=exception_data.exc_data["type"],
                exception_msg=exception_data.exc_data["msg"],
                exception_info=exception_data.exc_data["info"],
                stack_info=exception_data.exc_data["stack"],
            )
        )
        return data

    @staticmethod
    def get_request_log_data(
        request: Request, response: Response, start_time: int
    ) -> dict:
        # region 记录jwt
        jwt = request.headers.get("authorization")
        try:
            if jwt:
                payload = jwt.split(" ")[1].split(".")[1]
                payload = json.loads(
                    base64.b64decode(
                        payload + "=" * (-len(payload) % 4)
                    ).decode()
                )
                user = payload.get("user_id", None)
            else:
                user = (
                    request.user.id if request.user.is_authenticated else None
                )
        except Exception:
            user = None
        # endregion

        # region 记录请求参数
        request_param = request.GET.dict()

        request_data = {}
        file_data = {}
        try:
            for key, value in response.api_request_data.items():
                if isinstance(value, UploadedFile):
                    file_data[key] = {
                        "name": value.name,
                        "size": value.size,
                        "content_type": value.content_type,
                        "content_type_extra": value.content_type_extra,
                    }
                else:
                    request_data[key] = value
        except:
            pass
        # endregion

        # region 记录响应数据
        response_body = {}
        if response.get("content-type") in [
            "application/json",
            "application/vnd.api+json",
        ]:
            if getattr(response, "streaming", False):
                response_body = {"streaming": True}
            else:
                if type(response.content) == bytes:
                    response_body = json.loads(response.content.decode())
                else:
                    response_body = json.loads(response.content)
        # endregion

        # region 记录url
        if drf_logger_settings.PATH_TYPE == "ABSOLUTE":
            url = request.build_absolute_uri()
        elif drf_logger_settings.PATH_TYPE == "FULL_PATH":
            url = request.get_full_path()
        elif drf_logger_settings.PATH_TYPE == "RAW_URI":
            url = request.get_raw_uri()
        else:
            url = request.build_absolute_uri()
        # endregion

        headers = get_headers(request=request)
        method = request.method

        data = dict(
            user=user,
            ip=get_client_ip(request),
            method=method,
            url=url,
            headers=mask_sensitive_data(headers),
            content_type=request.content_type,
            query_param=mask_sensitive_data(request_param),
            request_body=mask_sensitive_data(request_data),
            file_data=file_data,
            response=mask_sensitive_data(response_body),
            status_code=response.status_code,
            execution_time=time.time() - start_time if start_time else None,
            create_time=timezone.now(),
        )

        return data
