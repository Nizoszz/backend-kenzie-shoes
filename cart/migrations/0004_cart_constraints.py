from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("cart", "0003_initial")]

    operations = [
        migrations.AddConstraint(
            model_name="cart",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantities__gt", 0)), name="cart_quantity_gt_0"
            ),
        ),
        migrations.AddConstraint(
            model_name="cart",
            constraint=models.UniqueConstraint(
                fields=("user", "product"), name="unique_user_product_cart"
            ),
        ),
    ]
