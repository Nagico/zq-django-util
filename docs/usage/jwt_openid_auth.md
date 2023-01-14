# JWT与OpenId认证

## 配置

将 `rest_framework_simplejwt` 添加到 `INSTALLED_APPS` 中：

```python
INSTALLED_APPS = [
    ...,
    "rest_framework_simplejwt",  # JWT,
]
```

并根据所需情况配置 `认证方式`

## 自定义配置

根据 [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html) 的文档进行配置：

```python
import datetime

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(days=10),
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
}
```

其中 `SIMPLE_JWT` 中的 `USER_ID_FIELD` 要与配置文件中 `USER_ID_FIELD` 一致（默认为 id）。

## 登录页面

### 认证视图集

在 `zq_django_util.utils.auth.views` 下有：

- `OpenIdLoginView` 用于 OpenId 认证，使用 `OpenIdLoginSerializer`

- `PasswordLoginView` 用于用户名-密码认证，使用 `PasswordLoginSerializer`

### 认证序列化器

该序列化器用于统一返回 Token 格式，包括：

```python
class TokenVO:
    id: int
    username: str
    access: str
    refresh: str
```

在 `zq_django_util.utils.auth.serializers` 下有：

- `OpenIdLoginSerializer` OpenId 登录序列化器

  调用 `OpenIdBackend` 认证后端，并在 OpenId 未绑定时抛出 `ThirdLoginFailed` 类型的 `ApiException`。

- `AbstractWechatLoginSerializer` 微信登录序列化器

  需要重写 `get_open_id` 方法，将 `code` 转化为 `openid` 返回

- `PasswordLoginSerializer` 用户名密码登录序列化器

  修改自 `TokenObtainPairSerializer`

### 认证后端使用

在 `zq_django_util.utils.auth.backends` 下有 `OpenIdBackend`，用于 OpenId 的认证流程。

需要在使用中调用 `authenticate` 方法，其中当参数 `raise_exception=True` 时，不兼容 Django 认证后端，但可以区分认证失败的相关异常。

在认证序列化器中可以捕获 `OpenIdNotBound`，并对未绑定的OpenId进行相关处理。

## 认证方式

在 `zq_django_util.utils.auth.authentications` 下有认证方式相关的类：

- `ActiveUserAuthentication` 允许激活的用户通过jwt登录

- `NormalUserAuthentication`  允许所有用户通过jwt登录

### 全局配置

在 `REST_FRAMEWORK__DEFAULT_AUTHENTICATION_CLASSES` 中可以配置全局的认证处理类：

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [  # 任何一个认证成功即可
        "zq_django_util.utils.auth.authentications.ActiveUserAuthentication",  # jwt: 激活用户认证方式
        "rest_framework.authentication.SessionAuthentication",  # session 认证，在 debug 中可以使用，用于 web 界面的登录
    ],
}
```

### 局部配置

在 view.py 视图集中可以覆盖配置 `authentication_classes`

```python
from zq_django_util.utils.auth.authentications import NormalUserAuthentication

authentication_classes = [NormalUserAuthentication]  # 允许所有用户通过jwt方式登录
```
