# 缓存视图 Mixin

## 自定义配置

设置缓存时间

在设置中添加 `CACHE_TTL`（秒），默认为 3600s。

## 使用Mixin

在视图集定义时使用：

- `CacheListModelMixin` 替换 `ListModelMixin`
- `CacheRetrieveModelMixin` 替换 `RetrieveModelMixin`
