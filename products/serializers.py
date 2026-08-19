from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from cart.serializers import ProductCartSerializer
from users.serializers import UserSerializer

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=50,
        validators=[UniqueValidator(queryset=Product.objects.all())],
    )

    class Meta:
        model = Product
        user = UserSerializer
        cart = ProductCartSerializer
        fields = [
            "id",
            "name",
            "value",
            "category",
            "stock",
            "description",
            "image_product",
            "user",
        ]

        read_only_fields = ["id", "user"]

    def create(self, validated_data):
        return Product.objects.create(**validated_data)
