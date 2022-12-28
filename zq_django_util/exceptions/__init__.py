import hashlib
import random
import time
import traceback
from sys import exc_info
from typing import Any, Dict, Optional

from django.conf import settings
from django.utils.timezone import now

from zq_django_util.response import ResponseType


class ApiException(Exception):
    """API异常"""

    def __init__(
        self,
        type: ResponseType,
        msg: Optional[str] = None,
        inner: Optional[Exception] = None,
        record: bool = False,
        detail: Optional[str] = None,
    ):
        """
        API异常
        :param type: 异常类型
        :param msg: 异常建议(面向用户)
        :param inner: 内部异常
        :param record: 是否记录异常
        :param detail: 异常详情(面向开发者)
        """
        self.record = record or type.get_status_code() == 500  # 是否记录异常(500强制记录)
        self.response_type: ResponseType = type
        if self.record:  # 记录异常
            self.eid = self.get_exp_id()  # 异常id
        else:
            self.eid = None
        self.detail = self.get_exp_detail(detail)  # 异常详情
        self.msg = self.get_exp_msg(msg)  # 异常用户提示
        self.event_id = None

        super().__init__(self.detail)

        self.inner = inner
        self.exc_data = None
        self.time = now()

    def get_exp_detail(self, detail: Optional[str]) -> str:
        """
        获取异常详情(面向开发者)
        :param detail: 自定义异常详情
        :return: 异常详情
        """
        res = detail or self.response_type.get_detail()  # 获取异常详情
        if self.record:  # 记录异常
            res = f"{res}, {self.eid}"  # 将自定义异常详情添加到末尾
        return res

    def get_exp_msg(self, msg: Optional[str]) -> str:
        """
        获取异常用户提示(面向用户)
        :param msg: 自定义异常用户提示
        :return: 异常用户提示
        """
        if self.record:  # 记录异常
            res = f"服务器开小差了，请向工作人员反馈以下内容：{self.eid}"  # 标准用户提示
            if msg:  # 如果有自定义异常用户提示
                res = f"{res}, {msg}"  # 将自定义用户提示添加到末尾
        else:  # 不记录异常
            res = msg or self.response_type.get_detail()  # 获取异常详情
        return res

    def get_response_data(self) -> Dict[str, Any]:
        """
        获取响应数据
        :return: 响应数据
        """
        self.exc_data = self.get_exception_info()
        data = {
            "code": self.response_type.get_code(),
            "detail": self.detail,
            "msg": self.msg,
            "data": self.get_exception_data(),
        }
        return data

    @staticmethod
    def get_exp_id() -> str:
        """
        获取异常id
        :return: 异常id
        """
        sha = hashlib.sha1()
        exp_id = time.strftime("%Y%m%d%H%M%S") + "_%04d" % random.randint(
            0, 10000
        )
        sha.update(exp_id.encode("utf-8"))
        return sha.hexdigest()[:6]

    @staticmethod
    def get_exception_info() -> Dict[str, Any]:
        """
        获取异常信息
        :return: 异常信息
        """
        exc_type, exc_value, exc_traceback_obj = exc_info()
        return {
            "type": str(exc_type),
            "msg": str(exc_value),
            "info": traceback.format_exc(),
            "stack": traceback.format_stack(),
        }

    def get_exception_data(self) -> Dict[str, Any]:
        """
        获取异常返回数据
        :return: 返回数据
        """
        data = {
            "eid": self.eid,
            "time": self.time,
        }

        if settings.DEBUG:
            data["exception"] = self.exc_data

        return data
