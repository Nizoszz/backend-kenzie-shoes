import pytest
from django.db import IntegrityError, transaction

from products.models import Product


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


# Create your tests here.
