from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("products", "0003_alter_product_name")]

    operations = [
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(("stock__gte", 0)), name="product_stock_gte_0"
            ),
        )
    ]
