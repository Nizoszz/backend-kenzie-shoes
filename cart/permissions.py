from rest_framework import permissions
from .models import Cart
from rest_framework.views import *


class IsBuyAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: View, obj: Cart) -> bool:
        return request.user.is_authenticated and obj.user_id == request.user.id
