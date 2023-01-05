<div align="center">

# zq-django-util
**自强 Studio Django 工具**

<!-- markdownlint-disable-next-line MD036 -->
</div>

<p align="center">
  <a href="https://github.com/Nagico/zq-django-util/actions/workflows/code_check.yml">
    <img src="https://github.com/Nagico/zq-django-util/actions/workflows/code_check.yml/badge.svg" alt="CI">
  </a>
  <a href="https://zq-django-util.readthedocs.io/en/latest/?badge=latest">
    <img src="https://readthedocs.org/projects/zq-django-util/badge/?version=latest" alt="Documentation Status" />
  </a>
  <a href="https://codecov.io/gh/Nagico/zq-django-util" >
    <img src="https://codecov.io/gh/Nagico/zq-django-util/branch/master/graph/badge.svg" alt="cov"/>
  </a>
  <a href="https://pypi.org/project/zq-django-util/">
  <img src="https://img.shields.io/pypi/v/zq-django-util" alt="pypi">
  </a>
</p>
<!-- markdownlint-enable MD033 -->

[English Version](README_EN.md)

## 简介

zq-django-util 是用于辅助搭建 django-drf 应用的工具集合，其中包含：

- 标准异常、响应处理
- jwt、微信认证
- oss 存储与直传
- 默认分页类
- 测试 ViewSet

详细文档：[zq-django-util.readthedocs.io](https://zq-django-util.readthedocs.io/)

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

可以根据以下说明进行配置，以启用相关功能。

[使用文档](docs/usage)

## 开发

本项目使用 Poetry 进行依赖管理，Pytest 进行单元测试。

[开发文档](docs/development)
