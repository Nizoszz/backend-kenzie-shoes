from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    CreateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from cart.serializers import ProductCartSerializer
from products.models import Product

from .models import Cart
from .permissions import IsBuyAccountOwner


class ProductCartView(CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = ProductCartSerializer
    queryset = Cart.objects.all()

    def perform_create(self, serializer):
        product = get_object_or_404(Product, id=self.kwargs.get("pk"))
        quantities = serializer.validated_data["quantities"]
        if self.queryset.filter(product=product, user=self.request.user).exists():
            raise ValidationError({"detail": "Produto já inserido no carrinho"})
        if quantities > product.stock:
            raise ValidationError({"detail": "Quantidade de produto indisponível"})
        serializer.save(product=product, user=self.request.user)


class ProductCartDetailView(RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsBuyAccountOwner]

    serializer_class = ProductCartSerializer
    queryset = Cart.objects.all()
