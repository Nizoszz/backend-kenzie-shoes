from rest_framework import permissions
from rest_framework.views import Request, View


class IsAdminAndSellerCreateUpdatedDestroy(permissions.BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            request.user.is_seller or request.user.is_staff
        )

    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or obj.user_id == request.user.id
