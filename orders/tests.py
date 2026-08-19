from decimal import Decimal

import pytest
from django.core import mail

from cart.models import Cart
from orders.models import UserOrder
from products.models import Product


def create_order(*, user, product, quantity=1):
    return UserOrder.objects.create(
        user=user,
        product=product,
        seller=product.user,
        quantity=quantity,
        unit_price=product.value,
        product_name=product.name,
        product_category=product.category,
        product_image=product.image_product,
    )


@pytest.mark.django_db(transaction=True)
def test_checkout_updates_stock_clears_cart_and_sends_email(
    authenticated_client, buyer, product, seller, django_capture_on_commit_callbacks
):
    second = Product.objects.create(
        name="Bota Teste",
        value="90.00",
        category="Botas",
        stock=3,
        description="Bota",
        image_product="https://example.com/bota.jpg",
        user=seller,
    )
    Cart.objects.create(user=buyer, product=product, quantities=2)
    Cart.objects.create(user=buyer, product=second, quantities=1)
    with django_capture_on_commit_callbacks(execute=True):
        response = authenticated_client(buyer).post(
            "/api/users/orders/", {}, format="json"
        )
    assert response.status_code == 201
    assert UserOrder.objects.filter(user=buyer).count() == 2
    assert not Cart.objects.filter(user=buyer).exists()
    product.refresh_from_db()
    second.refresh_from_db()
    assert (product.stock, second.stock) == (8, 2)
    first_order = UserOrder.objects.get(product=product)
    assert first_order.quantity == 2
    assert first_order.unit_price == product.value
    assert first_order.product_name == product.name
    assert first_order.total_price == product.value * 2
    assert len(mail.outbox) == 1


@pytest.mark.django_db(transaction=True)
def test_email_failure_does_not_fail_committed_checkout(
    authenticated_client,
    buyer,
    product,
    django_capture_on_commit_callbacks,
    monkeypatch,
):
    Cart.objects.create(user=buyer, product=product, quantities=1)

    def unavailable_mail(*args, **kwargs):
        raise ConnectionError("SMTP unavailable")

    monkeypatch.setattr("orders.services.send_mail", unavailable_mail)
    with django_capture_on_commit_callbacks(execute=True):
        response = authenticated_client(buyer).post("/api/users/orders/", {})

    assert response.status_code == 201
    assert UserOrder.objects.filter(user=buyer).exists()
    assert not Cart.objects.filter(user=buyer).exists()


@pytest.mark.django_db
def test_empty_cart_and_insufficient_stock_do_not_create_orders(
    authenticated_client, buyer, product
):
    client = authenticated_client(buyer)
    assert client.post("/api/users/orders/", {}).status_code == 400
    Cart.objects.create(user=buyer, product=product, quantities=5)
    product.stock = 2
    product.save()
    response = client.post("/api/users/orders/", {})
    assert response.status_code == 400
    assert UserOrder.objects.count() == 0
    assert Cart.objects.filter(user=buyer).exists()


@pytest.mark.django_db
def test_buyer_cannot_choose_order_status(authenticated_client, buyer, product):
    Cart.objects.create(user=buyer, product=product, quantities=1)
    response = authenticated_client(buyer).post(
        "/api/users/orders/", {"status": "Entregue"}, format="json"
    )
    assert response.status_code == 201
    assert UserOrder.objects.get(user=buyer).status == "Em andamento"


@pytest.mark.django_db
def test_buy_and_sell_lists_are_scoped(authenticated_client, buyer, product, make_user):
    other_buyer = make_user()
    own_order = create_order(user=buyer, product=product)
    create_order(user=other_buyer, product=product)
    buy_response = authenticated_client(buyer).get("/api/users/buyorders/")
    assert [item["id"] for item in buy_response.data["results"]] == [own_order.id]
    sell_response = authenticated_client(product.user).get("/api/users/sellorders/")
    assert sell_response.data["count"] == 2


@pytest.mark.django_db
def test_only_product_seller_can_update_order(
    authenticated_client, buyer, product, make_user
):
    order = create_order(user=buyer, product=product)
    intruder = make_user(is_seller=True)
    assert (
        authenticated_client(intruder)
        .patch(f"/api/users/orders/{order.id}/", {"status": "Entregue"}, format="json")
        .status_code
        == 403
    )
    response = authenticated_client(product.user).patch(
        f"/api/users/orders/{order.id}/", {"status": "Entregue"}, format="json"
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_order_snapshot_survives_product_changes_and_deletion(buyer, product):
    order = create_order(user=buyer, product=product, quantity=3)
    original_name = product.name
    original_price = Decimal(str(product.value))
    seller = product.user

    product.name = "Nome alterado depois da compra"
    product.value = "999.99"
    product.save(update_fields=("name", "value"))
    product.delete()

    order.refresh_from_db()
    assert order.product is None
    assert order.seller == seller
    assert order.product_name == original_name
    assert order.unit_price == original_price
    assert order.quantity == 3
    assert order.total_price == original_price * 3


@pytest.mark.django_db
def test_order_api_keeps_legacy_aliases_and_exposes_canonical_snapshot(
    authenticated_client, buyer, product
):
    order = create_order(user=buyer, product=product, quantity=2)

    response = authenticated_client(buyer).get("/api/users/buyorders/")
    payload = response.data["results"][0]

    assert payload["id"] == order.id
    assert payload["product"] == product.id
    assert payload["products"] == product.id
    assert payload["purchased_at"] == payload["buyed_at"]
    assert payload["quantity"] == 2
    expected_price = Decimal(str(product.value))
    assert payload["unit_price"] == f"{expected_price:.2f}"
    assert payload["total_price"] == f"{expected_price * 2:.2f}"


# Create your tests here.
