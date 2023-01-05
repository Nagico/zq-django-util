# 标准异常与响应处理+日志记录

## 配置

1.将 `REST_FRAMWORK__EXCEPTION_HANDLER` 设置为 `zq_django_util.exceptions.handler.exception_handler`，

将 `zq_django_util.response.renderers.CustomRenderer` 添加到 `DEFAULT_RENDERER_CLASSES` 首位：

```python
REST_FRAMEWORK = {
    # 异常处理
    "EXCEPTION_HANDLER": "zq_django_util.exceptions.handler.exception_handler",
    # 自定义渲染器
    "DEFAULT_RENDERER_CLASSES": [
        "zq_django_util.response.renderers.CustomRenderer",
        ...,
    ],
}
```

2.将 `drf_standardized_errors`、`zq_django_util.logs` 添加到 `INSTALLED_APPS` 中：

```python
INSTALLED_APPS = [
    ...,
    "drf_standardized_errors",
    "zq_django_util.logs",  # 日志应用
]
```

3.将 `zq_django_util.logs.middleware.APILoggerMiddleware` 添加到 `MIDDLEWARE` 中：

```python
MIDDLEWARE = [
    ...,
    "zq_django_util.logs.middleware.APILoggerMiddleware",  # 请求日志
]
```

4.在 `ROOT_URLCONF` 中设置：

```python
handler404 = "zq_django_util.exceptions.views.bad_request"
handler500 = "zq_django_util.exceptions.views.server_error"
```

### 自定义配置

### Sentry 配置

SENTRY_ENABLE = True/False

该配置将会影响 handler 中 sentry 通知的运行

#### ZQ_EXCEPTION 异常配置

默认值：

```python
ZQ_EXCEPTION = {
    "EXCEPTION_UNKNOWN_HANDLE": True,
    "EXCEPTION_HANDLER_CLASS": "zq_django_util.exceptions.handler.ApiExceptionHandler",
}
```

- `EXCEPTION_UNKNOWN_HANDLE` 是否处理未知异常

  若需便于调试，可以与 DEBUG 的值相反

- `EXCEPTION_HANDLER_CLASS` exception_handler 中使用的类

  默认为 `ApiExceptionHandler`，可以重写 `notify_sentry` 方法，自定义 sentry 通知内容

#### DRF_LOGGER 日志配置

默认值：

```python
DRF_LOGGER = {
    "DEFAULT_DATABASE": "default",
    "QUEUE_MAX_SIZE": 50,
    "INTERVAL": 10,
    "DATABASE": False,
    "PATH_TYPE": "FULL_PATH",
    "SKIP_URL_NAME": [],
    "SKIP_NAMESPACE": [],
    "METHODS": None,
    "STATUS_CODES": None,
    "SENSITIVE_KEYS": ["password", "token", "access", "refresh"],
    "ADMIN_SLOW_API_ABOVE": 500,
    "ADMIN_TIMEDELTA": 0,
}
```

- `DEFAULT_DATABASE` 写入的数据库

- `QUEUE_MAX_SIZE` 批量写入等待时的最大队列长度

  待解析日志数量超过当前值时，将批量解析并插入数据库

- `INTERVAL` 批量写入等待间隔

  超过当前时间间隔后将开始批量解析队列中的日志并插入数据库

- `DATABASE` 是否启用本地数据库记录

- `PATH_TYPE` 记录 url 类型

  `FULL_PATH`: 域名后面的所有内容，如 `/test/?foo=bar`

  `RAW_URI`: 原始 url，如 `http://testsetver/test/?foo=bar`

- `SKIP_URL_NAME` 跳过记录的 url name

  对应 drf 中的路径，注册 viewset 时指定 `basename`：

```python
router.register("api", APIRootViewSet, basename="test")
```
  method 是视图集中的方法（默认：list, retrieve, update, delete；以及自定义 action 装饰器下的方法名）

  则对应的 url name 为 `{basename}-{method}`

- `SKIP_NAMESPACE` 跳过记录的 namespace

  在 include 时定义 `namespace`：

```python
path(
      "test/",
      include("tests.urls", namespace="namespace"),
  ),
```

  其中 `__debug__`（django debug toolbar）与 `admin`（后台界面）始终跳过

- `METHODS` 需要记录的方法

  可选：

```python
["GET", "POST", "PUT", "PATCH", "DELETE", "OPTION"]
```
  当为空列表时，则全部都不记录；当为 None 时，则全部记录

- `STATUS_CODES` 需要记录的状态码

  当为空列表时，则全部都不记录；当为 None 时，则全部记录

- `SENSITIVE_KEYS` 敏感数据 key

  当请求、响应数据 key-val 中 key 在其出现，则自动用 value 的长度代替敏感内容存储

- `ADMIN_SLOW_API_ABOVE` admin 界面中筛选时 slow performance 的定义，单位毫秒

- `ADMIN_TIMEDELTA` admin 界面中展示时间间隔，单位分钟

## 响应

全局响应将会做以下包装：

```python
from zq_django_util.response.types import JSONVal

class ResponseData:
    code: str  # 响应码
    detail: str  # 响应的解释（面向开发者）
    msg: str  # 提醒、建议类消息（面向用户）
    data: JSONVal  # 响应内容
```
其中当响应正常时，`code` 为 `000000`，`detail` 与 `msg` 为 `""`。当出现异常时，会根据错误码表格中的数据进行自动填写默认值。

## 异常

全局异常处理会将已知的 `Django`、`DRF` 异常转换为具有响应格式语义的 `ApiException`。

### ApiException

在代码编写中也可以抛出 `ApiException` 以获得对应的异常响应

例如：

```python
from zq_django_util.exceptions import ApiException
from zq_django_util.response import ResponseType

try:
    0 / 0
except Exception as e:
    raise ApiException(
        # 使用已定义的 response type:
        # 若存在为定义的异常，可以申请异常码或使用 ServerError
        ResponseType.ParamValidationFailed,
        msg="msg: 您输入的参数有误，请检查后重试",  # 自定义 msg，若不赋值则使用 response type 默认的值
        detail="detail: 参数错误",  # 自定义 detail，若不赋值则使用 response type 默认的值
        inner=e,  # 内部异常，如果有可以填进去，便于 debug
        record=True  # 是否记录到数据库，如果记录了会有一个异常id展示给用户，便于错误排查
    )
```
响应：

```json
{
  "code": "A0430",
  "detail": "detail: 参数错误, 72580e",
  "msg": "msg: 您输入的参数有误，请检查后重试，请向工作人员反馈以下内容：72580e",
  "data": {
      "eid": "72580e",  // 异常 ID
      "time": "2023-01-05T06:16:24.787962Z",  // 时间
      "exception": {  // 异常相关信息（仅在 debug = True 时提供）
        // 异常类型 type(exc)
        "type": "<class 'zq_django_util.exceptions.ApiException'>",
        // 异常内容 str(exc)
        "msg": "detail: 参数错误, 72580e",
        // 异常详情 从异常context中获得
        "info": "Traceback (most recent call last):\n  File \"...views.py\", line 145, in api_exception\n    0 / 0\nZeroDivisionError: division by zero\n\nDuring handling of the above exception, another exception occurred:\n\nTraceback (most recent call last):\n  File \"...views.py\", line 506, in dispatch\n    response = handler(request, *args, **kwargs)\n  File \"...views.py\", line 147, in api_exception\n    raise ApiException(\nzq_django_util.exceptions.ApiException: detail: 参数错误, 72580e\n",
        // 完整异常调用栈 从异常context中获得
        "stack": []
    },
    "details": "division by zero",  // 内部异常详情
    "event_id": null  // sentry 事件 id，未开启 sentry 则为 null
  }
}
```

### 未知异常

如果遇到未处理的异常（即在 django、drf与apiexception 外的异常），会根据 `ZQ_EXCEPTION__EXCEPTION_UNKNOWN_HANDLE` 的设定进行相关处理：

- 处理未知异常，则将其转化为 ServerError

  响应：

```json
{
  "code": "B0000",
  "detail": "系统执行出错, b78bfd",
  "msg": "服务器开小差了，请向工作人员反馈以下内容：b78bfd",
  "data": {
    "eid": "b78bfd",
    "time": "2023-01-05T06:55:33.655749Z",
    "exception": {
      "type": "<class 'ZeroDivisionError'>",
      "msg": "division by zero",
      "info": "...",
      "stack": []
    },
    "details": {
        "type": "server_error",
        "errors": [
            {
                "code": "error",
                "detail": "division by zero",
                "attr": null
            }
        ]
    },
    "event_id": null
  }
}
```

- 不处理未知异常，则交给 Django 处理（可用于 DEBUG 时的显示异常详情界面）
