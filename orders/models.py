from django.db import models


class OrderStatus(models.TextChoices):
    REALIZADO = "Realizado"
    ANDAMENTO = "Em andamento"
    ENTREGUE = "Entregue"


class UserOrder(models.Model):
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.ANDAMENTO
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    product_name = models.CharField(max_length=50)
    product_category = models.CharField(max_length=20, blank=True)
    product_image = models.URLField(max_length=200, blank=True)

    user = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, related_name="user_order"
    )

    product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    seller = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sales",
    )

    class Meta:
        ordering = ("-purchased_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0), name="order_quantity_gt_0"
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0), name="order_unit_price_gte_0"
            ),
        ]

    def __str__(self):
        return f"Pedido #{self.pk} - {self.product_name}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity
