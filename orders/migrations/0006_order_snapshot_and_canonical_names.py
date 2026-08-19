from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def populate_order_snapshots(apps, schema_editor):
    UserOrder = apps.get_model("orders", "UserOrder")
    for order in UserOrder.objects.select_related("product", "product__user").iterator():
        product = order.product
        if product is None:
            continue
        order.seller_id = product.user_id
        order.quantity = 1
        order.unit_price = product.value
        order.product_name = product.name
        order.product_category = product.category
        order.product_image = product.image_product
        order.save(
            update_fields=(
                "seller",
                "quantity",
                "unit_price",
                "product_name",
                "product_category",
                "product_image",
            )
        )


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0005_alter_userorder_status"),
        ("products", "0004_product_stock_constraint"),
        ("users", "0002_oidc_partner_and_optional_address"),
    ]

    operations = [
        migrations.RenameField(
            model_name="userorder",
            old_name="buyed_at",
            new_name="purchased_at",
        ),
        migrations.RenameField(
            model_name="userorder",
            old_name="products",
            new_name="product",
        ),
        migrations.AddField(
            model_name="userorder",
            name="quantity",
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="userorder",
            name="unit_price",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0"), max_digits=12
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="userorder",
            name="product_name",
            field=models.CharField(default="", max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="userorder",
            name="product_category",
            field=models.CharField(blank=True, default="", max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="userorder",
            name="product_image",
            field=models.URLField(blank=True, default="", max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="userorder",
            name="seller",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sales",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(populate_order_snapshots, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="userorder",
            name="product",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to="products.product",
            ),
        ),
        migrations.AlterField(
            model_name="userorder",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="user_order",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterModelOptions(
            name="userorder",
            options={"ordering": ("-purchased_at", "-id")},
        ),
        migrations.AddConstraint(
            model_name="userorder",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gt", 0)), name="order_quantity_gt_0"
            ),
        ),
        migrations.AddConstraint(
            model_name="userorder",
            constraint=models.CheckConstraint(
                condition=models.Q(("unit_price__gte", 0)),
                name="order_unit_price_gte_0",
            ),
        ),
    ]
