from rest_framework import routers

from tests.sites.views import (
    TestCacheViewSet,
    TestCacheWithoutPaginationViewSet,
)

router = routers.SimpleRouter()

router.register("users", TestCacheViewSet, basename="test")
router.register(
    "users_no_page", TestCacheWithoutPaginationViewSet, basename="test_no_page"
)

urlpatterns = [
    *router.urls,
]
