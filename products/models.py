from django.db import models


class Category(models.TextChoices):
    BOTAS = ("Botas",)
    CHINELOS_SANDALIAS = ("Chinelos e Sandálias",)
    CHUTEIRAS = ("Chuteiras",)
    SAPATENIS = ("Sapatênis",)
    TENIS = ("Tênis",)
    TENIS_CORRIDA = ("Tênis de corrida",)


class Product(models.Model):
    name = models.CharField(max_length=50, unique=True)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.BOTAS
    )
    stock = models.IntegerField(default=0)
    description = models.TextField()
    image_product = models.URLField(max_length=200)
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="user_product",
    )

    class Meta:
        ordering = ("id",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stock__gte=0), name="product_stock_gte_0"
            )
        ]
