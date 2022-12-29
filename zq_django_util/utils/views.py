from typing import Any

from django.utils import timezone
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class APIRootViewSet(ListModelMixin, GenericViewSet):
    """
    API root view.
    """

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        time = timezone.localtime().isoformat()

        if user.is_anonymous:
            return Response(
                dict(
                    user=dict(
                        id=None,
                        username=None,
                        is_active=None,
                        is_superuser=None,
                    ),
                    time=time,
                )
            )
        else:
            return Response(
                dict(
                    user=dict(
                        id=user.id,
                        username=user.username,
                        is_active=user.is_active,
                        is_superuser=user.is_superuser,
                    ),
                    time=time,
                )
            )
