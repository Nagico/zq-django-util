from typing import TYPE_CHECKING, Any

from rest_framework.permissions import SAFE_METHODS, BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class ReadOnly(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.method in SAFE_METHODS


class CreateOnly(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.method in ["POST", "HEAD", "OPTIONS"]


class IsSuperUser(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_superuser

    def has_object_permission(
        self, request: Request, view: APIView, obj: Any
    ) -> bool:
        return request.user.is_superuser
