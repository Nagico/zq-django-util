"""
URLConf for test suite.
"""
from rest_framework import routers

router = routers.SimpleRouter()

urlpatterns = []

urlpatterns += router.urls

handler404 = "zq_django_util.exceptions.views.bad_request"
handler500 = "zq_django_util.exceptions.views.server_error"
