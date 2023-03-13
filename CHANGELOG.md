# Changelog

## v0.1.10 (2023-03-13)

#### New Features

* (log): 优化 admin 界面
#### Fixes

* (log): 修复数据库定时插入失败

Full set of changes: [`v0.1.9...v0.1.10`](https://github.com/Nagico/zq-django-util/compare/v0.1.9...v0.1.10)

## v0.1.9 (2023-03-07)

#### New Features

* (auth): 支持openid自定义字段验证

Full set of changes: [`v0.1.8...v0.1.9`](https://github.com/Nagico/zq-django-util/compare/v0.1.8...v0.1.9)

## v0.1.8 (2023-03-06)

#### New Features

* 添加RefreshTokenInvalid异常类型

Full set of changes: [`v0.1.7...v0.1.8`](https://github.com/Nagico/zq-django-util/compare/v0.1.7...v0.1.8)

## v0.1.7 (2023-03-04)

#### Fixes

* (auth): 修复token过期时间返回

Full set of changes: [`v0.1.6...v0.1.7`](https://github.com/Nagico/zq-django-util/compare/v0.1.6...v0.1.7)

## v0.1.6 (2023-03-01)

#### New Features

* (auth): 认证序列化器支持自定义返回内容
* 测试视图支持自定义用户数据返回
* (oss): 支持object acl
* 添加django example project
* (user): 支持oss自动文件清除
#### Fixes

* (log): 更新log字段
#### Others

* bump version to v0.1.5

Full set of changes: [`v0.1.5...v0.1.6`](https://github.com/Nagico/zq-django-util/compare/v0.1.5...v0.1.6)

## v0.1.5 (2023-02-27)

#### Fixes

* (log): 修复响应耗时记录错误

Full set of changes: [`v0.1.4...v0.1.5`](https://github.com/Nagico/zq-django-util/compare/v0.1.4...v0.1.5)

## v0.1.4 (2023-02-01)

#### Fixes

* (exception): 添加jwt异常处理

Full set of changes: [`v0.1.3...v0.1.4`](https://github.com/Nagico/zq-django-util/compare/v0.1.3...v0.1.4)

## v0.1.3 (2023-01-27)

#### New Features

* (auth): 添加验证后端自定义模型

Full set of changes: [`v0.1.2...v0.1.3`](https://github.com/Nagico/zq-django-util/compare/v0.1.2...v0.1.3)

## v0.1.2 (2023-01-14)

#### Fixes

* (mkdocs): 删除include插件
#### Docs

* (mkdocs): 支持readthedocs
* (mkdocs): 添加mkdocs构建支持

Full set of changes: [`v0.1.1...v0.1.2`](https://github.com/Nagico/zq-django-util/compare/v0.1.1...v0.1.2)

## v0.1.1 (2023-01-05)

#### New Features

* 添加 conventional commit 检测
#### Fixes

* (exception): 修复sentry通知检测
* (exception): 修复未知异常处理
* (exception): 修复异常记录时null字段
* (exception): 修复异常处理返回类型
* 更新github release发布
* (actions): 减少单测数量
#### Docs

* 更新readme
* 更新文档

Full set of changes: [`v0.1.0...v0.1.1`](https://github.com/Nagico/zq-django-util/compare/v0.1.0...v0.1.1)

## v0.1.0 (2023-01-04)

#### New Features

* (actions): 添加缓存优化
* 移除django3.2 drf3.12支持
* 添加poetry hook检查
* (oss): 取消django3.x中使用force_text
* (flake8): 使用pyproject配置
* 添加poetry支持
* (log): 取消日志记录强制安装sentry
* (test): 规范测试流程
* (user): 添加user默认排序
* (test): 添加PackageSettings单测
* (test): 添加测试默认用户类
* (log): 添加handler注释
* (log): 添加类型推断
* (log): 日志移除信号
* (exception): 更新记录异常时的msg提示
* (exception): 添加zq_exception配置
* (exception): 添加Api异常类测试
* (test): 添加测试模板
* (exception): 添加字符串模板
* (exception): 异常record参数覆盖'500状态码强制记录'
* (response): 响应类使用property替代方法
* 完善类型支持
* (exception): 异常生成工具支持pyi
* (exception): 更新异常内容
* 自动代码格式化
* 添加基础工具
#### Fixes

* (actions): 取消poetry cache
* (actions): poetry重复安装 设定config
* (actions): 取消python3.8 win测试
* (actions): 修复sqlite检测
* (actions): 取消自动poetry缓存
* (actions): 修复python版本判断
* (actions): python3.8 win下sqlite兼容json field
* 测试环境添加sentry-sdk
* (actions): 安装特殊版本依赖时只修改lock文件
* (actions): 使用test依赖进行测试
* (actions): 修复poetry依赖安装
* (actions): 修复python版本
* 兼容python3.8
* 兼容python3.9
* (response): 移除pyi支持
* (permission): 删除权限工具
* (exception): sentry调用兼容mock
* (response): 修复404界面
* (response): 修复property使用
* (exception): 定义异常Response类型
* (settings): 更新settings文件名字避免导入时与django重复
* (settings): 修复package setting重新加载设置的异常
* (exception): 修复反射时子类的判断
* (exception): 修复handler状态码获取
* 修复typing check时的循环导入
* (wechat): 删除微信相关util
#### Others

* 使用poetry管理, 合并其他配置
* (actions): 升级codecov版本
* 测试所有版本
* 添加github actions自动测试
* mit协议
* 添加flake8检测
* 格式化代码
