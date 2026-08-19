from rest_framework import serializers

from .models import OrderStatus, UserOrder


class OrderSerializer(serializers.ModelSerializer):
    user_buy = serializers.EmailField(source="user.email", read_only=True)
    status = serializers.ChoiceField(choices=OrderStatus.choices, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    # Aliases de leitura para clientes antigos. Novos clientes devem usar os
    # nomes canônicos ``purchased_at`` e ``product``.
    buyed_at = serializers.DateTimeField(source="purchased_at", read_only=True)
    products = serializers.PrimaryKeyRelatedField(source="product", read_only=True)

    class Meta:
        model = UserOrder
        fields = [
            "id",
            "status",
            "purchased_at",
            "product",
            "quantity",
            "unit_price",
            "total_price",
            "product_name",
            "product_category",
            "product_image",
            "seller",
            # Compatibilidade temporária com o contrato anterior.
            "buyed_at",
            "user_buy",
            "products",
        ]

        read_only_fields = fields


class OrderStatusSerializer(serializers.ModelSerializer):
    user_buy = serializers.EmailField(source="user.email", read_only=True)
    total_price = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    buyed_at = serializers.DateTimeField(source="purchased_at", read_only=True)
    products = serializers.PrimaryKeyRelatedField(source="product", read_only=True)

    class Meta:
        model = UserOrder
        fields = [
            "id",
            "status",
            "purchased_at",
            "product",
            "quantity",
            "unit_price",
            "total_price",
            "product_name",
            "product_category",
            "product_image",
            "seller",
            "buyed_at",
            "user_buy",
            "products",
        ]
        read_only_fields = [
            "id",
            "purchased_at",
            "product",
            "quantity",
            "unit_price",
            "total_price",
            "product_name",
            "product_category",
            "product_image",
            "seller",
            "buyed_at",
            "user_buy",
            "products",
        ]
