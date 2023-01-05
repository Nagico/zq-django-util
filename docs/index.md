# zq-django-util 文档

## 简介

zq-django-util 是用于辅助搭建 django-drf 应用的工具集合，其中包含：

- 标准异常、响应处理
- jwt、微信认证
- oss 存储与直传
- 默认分页类
- 测试 ViewSet

## 依赖需求

- Python 3.8+
- Django 3.2+
- Django REST framework 3.12+

**强烈建议**使用官方支持的最新版本，当前的测试环境为：Python 3.10, Django 4.1, DRF 3.14

## 安装

- 安装 zq-django-util 包

使用 `pip` 安装：
```shell
pip install zq-django-util
```

使用 `poetry` 安装：
```shell
poetry add zq-django-util
```

## 使用

可以根据以下说明进行配置，以启用相关功能

- [标准异常与响应处理+日志记录](usage/exception_response_log.md)
- [JWT与OpenId认证](usage/jwt_openid_auth.md)
- [OSS存储](usage/oss_storage.md)
- [缓存视图集Mixin](usage/cache_mixins.md)
- [分页](usage/pagination.md)
- [测试视图集](usage/test_viewset.md)

## 开发

本项目使用 Poetry 进行依赖管理，Pytest 进行单元测试。

[开发文档](development)
