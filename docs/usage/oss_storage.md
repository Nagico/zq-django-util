# OSS 存储使用

## 配置

```python
# region 媒体文件
MEDIA_URL = "/media/"
# endregion

# region oss
DEFAULT_FILE_STORAGE = "zq_django_util.utils.oss.backends.OssMediaStorage"
```

- `MEDIA_URL` 媒体文件子目录

- `DEFAULT_FILE_STORAGE` 默认文件存储

## 自定义配置

默认值：

```python
ALIYUN_OSS = {
    "ACCESS_KEY_ID": "",
    "ACCESS_KEY_SECRET": "",
    "ENDPOINT": "https://oss-cn-shanghai.aliyuncs.com",
    "BUCKET_NAME": "",
    "URL_EXPIRE_SECOND": 60 * 60 * 24 * 30,
    "TOKEN_EXPIRE_SECOND": 60,
    "MAX_SIZE_MB": 100,
}
```

- `ACCESS_KEY_ID` 阿里云 access key id

- `ACCESS_KEY_SECRET` 阿里云 access key secret

  id 与 secret 对应的阿里云账号需要有相关 bucket 的读写权限

- `ENDPOINT` bucket 地点对应的 url 地址

- `BUCKET_NAME` 桶名称

- `URL_EXPIRE_SECOND` 文件 url token 有效期

  对于`私有读`权限的桶才需要配置

- `TOKEN_EXPIRE_SECOND` 直传 token 默认有效期

- `MAX_SIZE_MB` 直传默认最大大小

## 存储后端

在 `zq_django_util.utils.oss.backends` 中有三种存储后端：

- `OssStorage` 基础存储，提供各种操作

- `OssMediaStorage` Media 存储，根据 settings 中 MEDIA_URL 作为根目录进行操作

- `OssStaticStorage` Static 存储，根据 settings 中 STATIC_URL 作为根目录进行操作

## 工具函数

### 获取随机文件名

`zq_django_util.utils.oss.utils.get_random_name`

用于保留后缀名的随机文件名获取，格式为 `{时间 %Y%m%d%H%M%S}_{4位随机数}.{后缀名}`

### 直传 token 获取

`zq_django_util.utils.oss.utils.get_token`

需提供：

- key: 上传文件路径及文件名（例如: `\media\avatar\123.png`，需给出包括默认文件夹前缀的完整路径）

- callback: 回调内容，格式为 Dict[str, str]

- policy: 上传策略（可选，默认根据 key 限制上传文件路径与文件名，根据设置限制签名有效期与最大上传大小）

返回：

- OSSCallbackToken: 直传 Token

格式参考

```python
class OSSCallbackToken:
    OSSAccessKeyId: str
    host: str
    policy: str
    signature: str
    expire: str
    key: str
    callback: str
```

回调内容设置请参考：[服务端签名直传并设置上传回调概述](https://help.aliyun.com/document_detail/31927.html)

### 回调身份验证

`zq_django_util.utils.oss.utils.check_callback_signature`

需提供：

- request: 回调的请求内容

返回：

- bool: 检测结果

将根据 headers 中提供的签名校验回调 body 是否正常
