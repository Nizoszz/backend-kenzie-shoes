import pytest
from django.db import IntegrityError, transaction

from cart.models import Cart


@pytest.mark.django_db
def test_cart_rejects_invalid_or_excess_quantity(authenticated_client, buyer, product):
    client = authenticated_client(buyer)
    assert (
        client.post(f"/api/products/{product.id}/cart/", {"quantities": 0}).status_code
        == 400
    )
    assert (
        client.post(f"/api/products/{product.id}/cart/", {"quantities": 11}).status_code
        == 400
    )


@pytest.mark.django_db
def test_product_can_be_in_different_carts_but_not_duplicated(
    authenticated_client, buyer, product, make_user
):
    client = authenticated_client(buyer)
    assert (
        client.post(f"/api/products/{product.id}/cart/", {"quantities": 2}).status_code
        == 201
    )
    assert (
        client.post(f"/api/products/{product.id}/cart/", {"quantities": 1}).status_code
        == 400
    )
    other = make_user()
    assert (
        authenticated_client(other)
        .post(f"/api/products/{product.id}/cart/", {"quantities": 1})
        .status_code
        == 201
    )


@pytest.mark.django_db
def test_cart_database_constraints(buyer, product):
    Cart.objects.create(user=buyer, product=product, quantities=1)
    with pytest.raises(IntegrityError), transaction.atomic():
        Cart.objects.create(user=buyer, product=product, quantities=1)


@pytest.mark.django_db
def test_only_cart_owner_can_update_or_delete(
    authenticated_client, buyer, product, make_user
):
    cart = Cart.objects.create(user=buyer, product=product, quantities=1)
    other = make_user()
    assert (
        authenticated_client(other)
        .patch(f"/api/cart/{cart.id}/", {"quantities": 2}, format="json")
        .status_code
        == 403
    )
    assert (
        authenticated_client(buyer).delete(f"/api/cart/{cart.id}/").status_code == 204
    )


# Create your tests here.
