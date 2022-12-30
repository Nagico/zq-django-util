"""
URLConf for test suite.
"""
from rest_framework import routers

from zq_django_util.utils.views import APIRootViewSet

router = routers.SimpleRouter()

router.register("test", APIRootViewSet, basename="test")

urlpatterns = []

urlpatterns += router.urls

handler404 = "zq_django_util.exceptions.views.bad_request"
handler500 = "zq_django_util.exceptions.views.server_error"
