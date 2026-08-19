from rest_framework import permissions
from rest_framework.views import Request, View

from .models import Cart


class IsBuyAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: View, obj: Cart) -> bool:
        return request.user.is_authenticated and obj.user_id == request.user.id
