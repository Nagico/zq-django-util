# zq-django-util 开发文档

本项目使用 Poetry 进行依赖管理，Pytest 进行单元测试

## 依赖安装

推荐先使用 conda 创建新的虚拟环境，并进入其中

安装 poetry：
```shell
pip install poetry
```

安装开发依赖：
```shell
poetry install --with dev
```

## 项目结构
```
.github/  Github 相关配置
  workflows/  GitHub actions 配置
    code_check.yml  CI 代码检测

docs/  文档

scripts/  发布脚本
  1_generate_changelog.py  生成 change log
  2_bump_version_and_publish.py  更新 version 并发布

tests/  单元测试

utils/  工具类
  response_type_parser/  根据 error.ini 的内容更新 Response Type 代码
  windows_sqlite_fix/  修复 python 3.8 以下的 sqlite json 支持

zq_django_util/  项目主要代码

runtests.py  运行单测
```

## 单元测试

使用以下命令进行本地测试：
```shell
python runtests.py --coverage-local
```

单元测试覆盖率只会计算 `zq_django_util` 文件夹下的内容

本项目需要求覆盖率需要大于 96%

## 提交 Commit

请遵循 [conventional commit](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#-commit-message-guidelines) 进行代码提交

`type` 支持 feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

提交 commit 时会自动进行 black、isort 代码格式化，flake8 等代码格式检查，commit 格式检查

首次提交时需要下载相关检测代码，请耐心等待

提交时可能第一次不成功，是因为出现了格式错误：
- Console 中若提醒已自动修复，可以直接再次提交
- 若 Console 中仍存在错误，需对相关部分进行修改
