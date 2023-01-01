"""
URLConf for test suite.
"""
from django.contrib import admin
from django.urls import path
from rest_framework import routers

from zq_django_util.utils.views import APIRootViewSet

router = routers.SimpleRouter()

router.register("test", APIRootViewSet, basename="test")
router.register("", APIRootViewSet, basename="root")

urlpatterns = [
    path("admin/", admin.site.urls),  # admin 后台管理
    *router.urls,
]

handler404 = "zq_django_util.exceptions.views.bad_request"
handler500 = "zq_django_util.exceptions.views.server_error"
