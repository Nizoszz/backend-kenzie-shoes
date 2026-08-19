from rest_framework import permissions
from .models import User
from rest_framework.views import Request, View


class IsAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: View, obj: User) -> bool:
        return request.user.is_authenticated and obj == request.user


class IsAdminReadOnly(permissions.BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated and request.user.is_staff
        )
