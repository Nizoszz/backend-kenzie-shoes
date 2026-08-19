from django.db import models


class Cart(models.Model):
    quantities = models.IntegerField(default=1)
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="user_cart"
    )
    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="products_cart"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantities__gt=0), name="cart_quantity_gt_0"
            ),
            models.UniqueConstraint(
                fields=("user", "product"), name="unique_user_product_cart"
            ),
        ]
