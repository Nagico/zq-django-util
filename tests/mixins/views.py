from rest_framework.viewsets import GenericViewSet

from tests.mixins.serializers import UserSerializer
from tests.models import User
from zq_django_util.utils import mixins


class TestCacheViewSet(
    mixins.CacheListModelMixin, mixins.CacheRetrieveModelMixin, GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = ["username", "phone"]


class TestCacheWithoutPaginationViewSet(
    mixins.CacheListModelMixin, mixins.CacheRetrieveModelMixin, GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = None
