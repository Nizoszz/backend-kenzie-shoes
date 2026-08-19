from decimal import Decimal

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db(transaction=True)
def test_order_snapshot_data_migration_preserves_legacy_order():
    executor = MigrationExecutor(connection)
    old_target = [("orders", "0005_alter_userorder_status")]
    executor.migrate(old_target)
    old_apps = executor.loader.project_state(old_target).apps

    Address = old_apps.get_model("addresses", "Address")
    User = old_apps.get_model("users", "User")
    Product = old_apps.get_model("products", "Product")
    UserOrder = old_apps.get_model("orders", "UserOrder")

    address = Address.objects.create(
        street="Rua Histórica",
        number=10,
        zipcode="01000-000",
        city="São Paulo",
        state="SP",
    )
    seller = User.objects.create(
        username="legacy-seller",
        first_name="Legacy",
        last_name="Seller",
        email="legacy-seller@example.com",
        password="unusable",
        is_seller=True,
        address_id=address.id,
    )
    buyer = User.objects.create(
        username="legacy-buyer",
        first_name="Legacy",
        last_name="Buyer",
        email="legacy-buyer@example.com",
        password="unusable",
    )
    product = Product.objects.create(
        name="Tênis histórico",
        value=Decimal("149.90"),
        category="Tênis",
        stock=4,
        description="Produto anterior ao snapshot",
        image_product="https://example.com/historico.jpg",
        user_id=seller.id,
    )
    legacy_order = UserOrder.objects.create(user_id=buyer.id, products_id=product.id)

    executor = MigrationExecutor(connection)
    new_target = [("orders", "0006_order_snapshot_and_canonical_names")]
    executor.migrate(new_target)
    new_apps = executor.loader.project_state(new_target).apps
    MigratedOrder = new_apps.get_model("orders", "UserOrder")
    migrated = MigratedOrder.objects.get(pk=legacy_order.id)

    assert migrated.product_id == product.id
    assert migrated.seller_id == seller.id
    assert migrated.quantity == 1
    assert migrated.unit_price == Decimal("149.90")
    assert migrated.product_name == "Tênis histórico"
    assert migrated.product_category == "Tênis"
    assert migrated.product_image == "https://example.com/historico.jpg"
