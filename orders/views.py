import logging

from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from users.permissions import IsAccountOwner

from .models import UserOrder
from .permissions import IsSellerUser
from .serializers import OrderSerializer, OrderStatusSerializer
from .services import CheckoutError, checkout_cart

security_logger = logging.getLogger("commerce.security")


class OrderPaginator(PageNumberPagination):
    page_size = 10


class OrderView(CreateAPIView):
    throttle_scope = "checkout"
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = OrderSerializer
    queryset = UserOrder.objects.all().order_by("id")

    pagination_class = OrderPaginator

    def perform_create(self, serializer):
        try:
            orders = checkout_cart(self.request.user)
        except CheckoutError as error:
            raise ValidationError({"detail": str(error)}) from error
        serializer.instance = orders[-1]


class OrderDetailView(UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSellerUser]

    serializer_class = OrderStatusSerializer
    queryset = UserOrder.objects.all().order_by("id")

    def perform_update(self, serializer):
        order = self.queryset.get(id=self.kwargs.get("pk"))
        if not self.request.user.is_staff and order.seller_id != self.request.user.id:
            raise PermissionDenied("You do not have permission to perform this action.")
        serializer.save()
        security_logger.info(
            "order_status_updated order_id=%s actor_id=%s status=%s",
            order.id,
            self.request.user.id,
            serializer.instance.status,
        )


class BuyOrderView(ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAccountOwner]

    serializer_class = OrderSerializer
    queryset = UserOrder.objects.all().order_by("id")

    pagination_class = OrderPaginator

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)


class SellOrderView(ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSellerUser]

    serializer_class = OrderSerializer
    queryset = UserOrder.objects.all().order_by("id")

    pagination_class = OrderPaginator

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(seller=self.request.user)
