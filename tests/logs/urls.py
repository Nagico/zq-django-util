"""
URLConf for test suite.
"""
from typing import NamedTuple

from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from zq_django_util.utils.views import APIRootViewSet


class NamedURL(NamedTuple):
    urlconf_module: str
    app_name: str


router = routers.SimpleRouter()

router.register("test", APIRootViewSet, basename="test")

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "__debug__/",
        include(NamedURL("tests.urls", "debug"), namespace="__debug__"),
    ),
    path(
        "namespace/",
        include(NamedURL("tests.urls", "namespace"), namespace="namespace"),
    ),
    *router.urls,
]

handler404 = "zq_django_util.exceptions.views.bad_request"
handler500 = "zq_django_util.exceptions.views.server_error"
