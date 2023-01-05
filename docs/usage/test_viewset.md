# 测试视图集

## 配置
APIRootViewSet 可以提供一个测试界面，将其配置到 `urls.py` 内，即可访问。

## 响应

其响应结果如下（已开启标准异常与响应处理）：

- 匿名用户响应
```json5
{
  "code": "00000",
  "detail": "",
  "msg": "",
  "data": {
    "user": {
      "id": null,
      "username": null,
      "is_active": null,
      "is_superuser": null
    },
    "time": "2023-01-05T13:50:18.214604+08:00"
  }
}
```

- 普通用户响应
```json5
{
  "code": "00000",
  "detail": "",
  "msg": "",
  "data": {
    "user": {  // based on request.user
      "id": 1,
      "username": "co",
      "is_active": true,
      "is_superuser": true
    },
    "time": "2023-01-05T13:50:03.009733+08:00"
  }
}
```
