import base64
import datetime
import hashlib
import hmac
import json
from typing import Any, Optional, TypedDict
from urllib.parse import unquote
from urllib.request import urlopen

from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from django.conf import settings
from rest_framework.request import Request


class OSSCallbackToken(TypedDict):
    OSSAccessKeyId: str
    host: str
    policy: str
    signature: str
    expire: str
    key: str
    callback: str


def get_iso_8601(expire: float) -> str:
    gmt = datetime.datetime.utcfromtimestamp(expire).isoformat()
    gmt += "Z"
    return gmt


def get_token(
        key: str,
        callback: Optional[dict[str, str]],
        policy: Optional[dict[str, Any]] = None,
) -> OSSCallbackToken:
    """
    获取直传签名token
    """
    # 获取Policy
    expire_time = datetime.datetime.now() + datetime.timedelta(
        seconds=settings.ALIYUN_OSS_EXPIRATION_SECONDS
    )
    expire = get_iso_8601(expire_time.timestamp())
    if policy is None:
        policy = {
            "expiration": expire,  # 过期时间
            "conditions": [
                {"bucket": settings.ALIYUN_OSS_BUCKET_NAME},
                [
                    "content-length-range",
                    0,
                    settings.ALIYUN_OSS_MAX_SIZE_MB * 1024 * 1024,
                ],  # 限制上传文件大小
                ["eq", "$key", f"{key}"],  # 限制上传文件名
            ],
        }
    policy = json.dumps(policy).strip()
    policy_encode = base64.b64encode(policy.encode())

    # 签名
    h = hmac.new(
        settings.ALIYUN_OSS_ACCESS_KEY_SECRET.encode(),
        policy_encode,
        hashlib.sha1,
    )
    sign = base64.encodebytes(h.digest()).strip()

    # 回调参数
    callback_param = json.dumps(callback).strip()
    base64_callback_body = base64.b64encode(callback_param.encode())

    return dict(
        OSSAccessKeyId=settings.ALIYUN_OSS_ACCESS_KEY_ID,
        host=settings.ALIYUN_OSS_URL,
        policy=policy_encode.decode(),
        signature=sign.decode(),
        expire=expire,
        key=key,
        callback=base64_callback_body.decode(),
    )


def check_callback_signature(request: Request) -> bool:
    """
    检测回调身份
    """
    authorization_base64 = request.META.get(
        "HTTP_AUTHORIZATION", None
    )  # 获取AUTHORIZATION
    pub_key_url_base64 = request.META.get(
        "HTTP_X_OSS_PUB_KEY_URL", None
    )  # 获取公钥
    if authorization_base64 is None or pub_key_url_base64 is None:
        return False

    try:
        # 对x-oss-pub-key-url做base64解码后获取到公钥
        pub_key_url = base64.b64decode(pub_key_url_base64).decode()

        # 为了保证该public_key是由OSS颁发的，用户需要校验x-oss-pub-key-url的开头
        if not pub_key_url.startswith(
            "http://gosspublic.alicdn.com/"
        ) and not pub_key_url.startswith("https://gosspublic.alicdn.com/"):
            return False
        url_reader = urlopen(pub_key_url)
        # you can cache it
        pub_key = url_reader.read()
    except:
        return False

    # 获取base64解码后的签名
    authorization = base64.b64decode(authorization_base64)

    # 获取待签名字符串
    callback_body = request.body

    if request.META["QUERY_STRING"] == "":
        auth_str = (
            unquote(request.META["PATH_INFO"]) + "\n" + callback_body.decode()
        )
    else:
        auth_str = (
            unquote(request.META["PATH_INFO"])
            + "?"
            + request.META["QUERY_STRING"]
            + "\n"
            + callback_body.decode()
        )

    # 验证签名
    auth_md5 = MD5.new(auth_str.encode())
    rsa_pub = RSA.importKey(pub_key)
    try:
        verifier = PKCS1_v1_5.new(rsa_pub)
        verifier.verify(auth_md5, authorization)
        return True
    except:
        return False
