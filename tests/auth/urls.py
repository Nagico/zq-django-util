from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from zq_django_util.utils.auth.views import OpenIdLoginView, PasswordLoginView

urlpatterns = [
    path(
        "login/openid/", OpenIdLoginView.as_view(), name="openid_pair"
    ),  # openid登录
    path(
        "login/password/", PasswordLoginView.as_view(), name="password_login"
    ),  # 密码登录
    path(
        "refresh/", TokenRefreshView.as_view(), name="token_refresh"
    ),  # 刷新token
]
