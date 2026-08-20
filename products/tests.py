import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction

from products.management.commands.seed_shoes import SHOES
from products.models import Product
from users.models import User


@pytest.mark.django_db
def test_product_stock_database_constraint(product):
    product.stock = -1
    with pytest.raises(IntegrityError), transaction.atomic():
        product.save()


@pytest.mark.django_db
def test_product_list_is_public_and_filterable(api_client, product):
    response = api_client.get("/api/products/?name=teste&category=tênis")
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_only_seller_can_create_product(authenticated_client, buyer, seller):
    payload = {
        "name": "Bota Nova",
        "value": "120.00",
        "category": "Botas",
        "stock": 4,
        "description": "Nova",
        "image_product": "https://example.com/bota.jpg",
    }
    assert (
        authenticated_client(buyer).post("/api/products/", payload).status_code == 403
    )
    response = authenticated_client(seller).post("/api/products/", payload)
    assert response.status_code == 201
    assert Product.objects.get(name="Bota Nova").user == seller


@pytest.mark.django_db
def test_seller_cannot_change_another_sellers_product(
    authenticated_client, product, make_user
):
    other_seller = make_user(is_seller=True)
    response = authenticated_client(other_seller).patch(
        f"/api/products/{product.id}/", {"stock": 1}, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_seed_shoes_creates_catalog_and_is_idempotent(capsys):
    call_command("seed_shoes")

    seller = User.objects.get(username="demo-seller")
    assert seller.is_seller is True
    assert seller.has_usable_password() is False
    assert Product.objects.filter(user=seller).count() == len(SHOES)
    assert all(
        product.image_product.startswith("https://")
        for product in Product.objects.all()
    )

    call_command("seed_shoes")

    assert Product.objects.filter(user=seller).count() == len(SHOES)
    assert "0 criados" in capsys.readouterr().out


@pytest.mark.django_db
def test_seed_shoes_does_not_reset_existing_stock():
    call_command("seed_shoes")
    product = Product.objects.get(name=SHOES[0]["name"])
    product.stock = 1
    product.save(update_fields=("stock",))

    call_command("seed_shoes")

    product.refresh_from_db()
    assert product.stock == 1


@pytest.mark.django_db
def test_seed_shoes_does_not_promote_existing_buyer(buyer):
    with pytest.raises(CommandError, match="não possui perfil de vendedor"):
        call_command("seed_shoes", seller=buyer.username)

    buyer.refresh_from_db()
    assert buyer.is_seller is False
    assert Product.objects.count() == 0


# Create your tests here.
