import pytest
from django.core import mail

from cart.models import Cart
from orders.models import UserOrder
from products.models import Product


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
    own_order = UserOrder.objects.create(user=buyer, products=product)
    UserOrder.objects.create(user=other_buyer, products=product)
    buy_response = authenticated_client(buyer).get("/api/users/buyorders/")
    assert [item["id"] for item in buy_response.data["results"]] == [own_order.id]
    sell_response = authenticated_client(product.user).get("/api/users/sellorders/")
    assert sell_response.data["count"] == 2


@pytest.mark.django_db
def test_only_product_seller_can_update_order(
    authenticated_client, buyer, product, make_user
):
    order = UserOrder.objects.create(user=buyer, products=product)
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


# Create your tests here.
