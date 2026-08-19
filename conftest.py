import pytest
from rest_framework.test import APIClient

from addresses.models import Address
from products.models import Product
from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    counter = 0

    def factory(
        *, is_seller=False, is_staff=False, password="StrongPass123!", **kwargs
    ):
        nonlocal counter
        counter += 1
        address = Address.objects.create(
            street="Rua Teste",
            number=counter,
            zipcode="01000-000",
            city="São Paulo",
            state="SP",
        )
        username = kwargs.pop("username", f"user{counter}")
        return User.objects.create_user(
            username=username,
            email=kwargs.pop("email", f"{username}@example.com"),
            password=password,
            first_name=kwargs.pop("first_name", "Test"),
            last_name=kwargs.pop("last_name", "User"),
            address=address,
            is_seller=is_seller,
            is_staff=is_staff,
            **kwargs,
        )

    return factory


@pytest.fixture
def seller(make_user):
    return make_user(is_seller=True, username="seller")


@pytest.fixture
def buyer(make_user):
    return make_user(username="buyer")


@pytest.fixture
def product(seller):
    return Product.objects.create(
        name="Tênis Teste",
        value="199.90",
        category="Tênis",
        stock=10,
        description="Produto para testes",
        image_product="https://example.com/shoe.jpg",
        user=seller,
    )


@pytest.fixture
def authenticated_client(api_client):
    def authenticate(user):
        api_client.force_authenticate(user=user)
        return api_client

    return authenticate
