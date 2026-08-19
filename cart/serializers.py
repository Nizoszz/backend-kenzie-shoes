from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Cart


class ProductCartSerializer(serializers.ModelSerializer):
    def validate_quantities(self, value):
        if value <= 0:
            raise ValidationError("A quantidade deve ser maior que zero")
        product = getattr(self.instance, "product", None)
        if product is not None and value > product.stock:
            raise ValidationError({"detail": "Quantidade de produto indisponível"})
        return value

    class Meta:
        model = Cart
        fields = ["id", "quantities", "user_id", "product"]

        read_only_fields = ["id", "user_id", "product"]
