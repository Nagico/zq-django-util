<div align="center">

# zq-django-util
**Django Tool Sets for Ziqiang Studio**

<!-- markdownlint-disable-next-line MD036 -->
</div>

<p align="center">
  <a href="https://github.com/Nagico/zq-django-util/actions/workflows/code_check.yml">
    <img src="https://github.com/Nagico/zq-django-util/actions/workflows/code_check.yml/badge.svg" alt="CI">
  </a>
  <a href="https://codecov.io/gh/Nagico/zq-django-util" >
    <img src="https://codecov.io/gh/Nagico/zq-django-util/branch/master/graph/badge.svg" alt="cov"/>
  </a>
  <a href="https://pypi.org/project/zq-django-util/">
  <img src="https://img.shields.io/pypi/v/zq-django-util" alt="pypi">
  </a>
</p>
<!-- markdownlint-enable MD033 -->

## Overview

`zq-django-util` is a tool sets for build django-drf applications, which contains:

- Standard exception and response handler
- JWT and Wechat authentication
- Aliyun OSS Storage and upload directly in client
- Default pagination class
- Test ViewSet

## Requirements

- Python 3.8+
- Django 3.2+
- Django REST framework 3.12+

We **highly recommend** using the latest version. The test version we currently use is Python 3.10, Django 4.1, and DRF 3.14.

## Installation

- Install `zq-django-util` package

Install using `pip`:
```shell
pip install zq-django-util
```

Install using `poetry`:
```shell
poetry add zq-django-util
```

## Usage

[Usage Docs (CN)](https://github.com/Nagico/zq-django-util/blob/master/docs/usage)

## Contribute

We use Poetry and Pytest to build our project.

[Development Docs (CN)](https://github.com/Nagico/zq-django-util/blob/master/docs/development)
