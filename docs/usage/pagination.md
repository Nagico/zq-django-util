# 分页

提供 PageNumer 分页器 `zq_django_util.utils.pagination.GlobalPageNumberPagination`，使用 url query 参数控制：

- `page` 控制页数
- `page_size` 控制页大小，默认为 20，最大为 200

## 全局分页

如需开启默认分页，可以将 `REST_FRAMEWORK__DEFAULT_PAGINATION_CLASS` 设置为全局分页器：
```python
REST_FRAMEWORK = {
    # 分页
    "DEFAULT_PAGINATION_CLASS": "zq_django_util.utils.pagination.GlobalPageNumberPagination",
}
```

## 局部分页

在视图中可以局部控制分页：

- 开启分页
```python
from zq_django_util.utils.pagination import GlobalPageNumberPagination

pagination_class = GlobalPageNumberPagination
```

- 关闭分页
```python
pagination_class = None
```
