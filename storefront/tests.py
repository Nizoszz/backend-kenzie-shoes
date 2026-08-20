from decimal import Decimal

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from cart.models import Cart
from orders.models import UserOrder
from users.admin import PartnerApplicationAdmin
from users.models import OIDCIdentity, PartnerApplication

User = get_user_model()


@pytest.mark.django_db
def test_public_pages_render_and_dashboard_redirects(client, product):
    home = client.get("/")
    assert home.status_code == 200
    assert b"storefront/images/hero-shoes" in home.content
    response = client.get("/shop/?q=teste&category=Tênis")
    assert response.status_code == 200
    assert product.name.encode() in response.content
    assert b"data-auto-filter-form" in response.content
    assert b"data-filter-search" in response.content
    assert b"data-filter-category" in response.content
    assert b"Remover filtros" in response.content
    assert b">Filtrar</" not in response.content
    assert b"Remover filtros" not in client.get("/shop/").content
    assert client.get("/dashboard/").status_code == 302


def test_login_explains_when_oidc_is_not_configured(client, settings):
    settings.OIDC_SERVER_METADATA_URL = ""
    settings.OIDC_CLIENT_ID = ""
    response = client.get("/login/")
    assert response.status_code == 200
    assert b"Login externo indispon\xc3\xadvel" in response.content


def test_login_exposes_configured_oidc_provider(client, settings):
    settings.OIDC_SERVER_METADATA_URL = (
        "https://identity.example/.well-known/openid-configuration"
    )
    settings.OIDC_CLIENT_ID = "commerce-web"
    settings.OIDC_PROVIDER_NAME = "Empresa ID"
    response = client.get("/login/")
    assert response.status_code == 200
    assert b"Continuar com Empresa ID" in response.content


@pytest.mark.django_db
def test_local_registration_creates_session_and_argon2_password(client):
    response = client.post(
        "/register/",
        {
            "username": "web-user",
            "first_name": "Web",
            "last_name": "User",
            "email": "web@example.com",
            "password1": "VeryStrongPass123!",
            "password2": "VeryStrongPass123!",
            "street": "Rua Web",
            "number": 10,
            "zipcode": "01000-000",
            "city": "São Paulo",
            "state": "SP",
            "add_on": "",
        },
    )
    assert response.status_code == 302
    user = User.objects.get(username="web-user")
    assert user.password.startswith("argon2$")
    assert user.address.street == "Rua Web"
    assert client.get("/account/").status_code == 200


@pytest.mark.django_db
def test_logout_requires_post(client, buyer):
    client.force_login(buyer)
    assert client.get("/logout/").status_code == 405
    assert client.post("/logout/").status_code == 302


@pytest.mark.django_db
def test_incomplete_oidc_profile_cannot_add_to_cart(client, product):
    user = User.objects.create_user(
        username="incomplete", email="incomplete@example.com", password="StrongPass123!"
    )
    client.force_login(user)
    response = client.post(f"/cart/add/{product.id}/", {"quantities": 1})
    assert response.status_code == 302
    assert not Cart.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_cart_is_scoped_and_checkout_uses_shared_service(client, buyer, product):
    client.force_login(buyer)
    assert client.post(f"/cart/add/{product.id}/", {"quantities": 2}).status_code == 302
    item = Cart.objects.get(user=buyer)
    assert client.post(f"/cart/{item.id}/update/", {"quantities": 3}).status_code == 302
    assert client.post("/checkout/").status_code == 302
    order = UserOrder.objects.get(user=buyer, product=product)
    assert order.quantity == 3
    assert order.unit_price == Decimal(str(product.value))
    product.refresh_from_db()
    assert product.stock == 7


@pytest.mark.django_db
def test_partner_application_requires_admin_approval(client, buyer, make_user):
    client.force_login(buyer)
    assert (
        client.post(
            "/partner/apply/", {"message": "Tenho uma loja de calçados autorais."}
        ).status_code
        == 302
    )
    application = PartnerApplication.objects.get(user=buyer)
    assert application.status == PartnerApplication.Status.PENDING
    assert not buyer.is_seller

    admin_user = make_user(username="admin-review", is_staff=True, is_superuser=True)
    request = RequestFactory().post("/admin/")
    request.user = admin_user
    PartnerApplicationAdmin(PartnerApplication, AdminSite()).approve(
        request, PartnerApplication.objects.filter(pk=application.pk)
    )
    buyer.refresh_from_db()
    assert buyer.is_seller


@pytest.mark.django_db
def test_only_seller_can_access_seller_area(client, buyer, seller):
    client.force_login(buyer)
    assert client.get("/seller/").status_code == 403
    client.force_login(seller)
    assert client.get("/seller/").status_code == 200


class FakeOIDCClient:
    def __init__(self, claims):
        self.claims = claims

    def authorize_access_token(self, request):
        return {"userinfo": self.claims}


@pytest.mark.django_db
def test_oidc_login_uses_configured_callback(client, monkeypatch, settings):
    captured = {}

    class FakeAuthorizeClient:
        def authorize_redirect(self, request, redirect_uri):
            captured["redirect_uri"] = redirect_uri
            from django.shortcuts import redirect

            return redirect("https://identity.example/authorize")

    settings.OIDC_SERVER_METADATA_URL = (
        "https://identity.example/.well-known/openid-configuration"
    )
    settings.OIDC_CLIENT_ID = "commerce-web"
    settings.OIDC_REDIRECT_URI = "https://shop.example/auth/oidc/callback/"
    monkeypatch.setattr("storefront.views.oidc_client", lambda: FakeAuthorizeClient())

    response = client.get("/auth/oidc/login/")

    assert response.status_code == 302
    assert response.url == "https://identity.example/authorize"
    assert captured["redirect_uri"] == settings.OIDC_REDIRECT_URI


@pytest.mark.django_db
def test_oidc_creates_incomplete_user_without_local_password(client, monkeypatch):
    claims = {
        "sub": "oidc-123",
        "email": "oidc@example.com",
        "email_verified": True,
        "given_name": "OIDC",
        "family_name": "User",
    }
    monkeypatch.setattr("storefront.views.oidc_client", lambda: FakeOIDCClient(claims))
    response = client.get("/auth/oidc/callback/")
    assert response.status_code == 302
    user = User.objects.get(email="oidc@example.com")
    assert not user.has_usable_password()
    assert not user.profile_complete
    assert OIDCIdentity.objects.filter(user=user, subject="oidc-123").exists()


@pytest.mark.django_db
def test_oidc_rejects_unverified_email_and_email_collision(client, monkeypatch, buyer):
    unverified = {"sub": "bad", "email": "bad@example.com", "email_verified": False}
    monkeypatch.setattr(
        "storefront.views.oidc_client", lambda: FakeOIDCClient(unverified)
    )
    assert client.get("/auth/oidc/callback/").status_code == 302
    assert not User.objects.filter(email="bad@example.com").exists()

    collision = {"sub": "collision", "email": buyer.email, "email_verified": True}
    monkeypatch.setattr(
        "storefront.views.oidc_client", lambda: FakeOIDCClient(collision)
    )
    client.get("/auth/oidc/callback/")
    assert not OIDCIdentity.objects.filter(subject="collision").exists()


@pytest.mark.django_db
def test_authenticated_user_can_explicitly_link_oidc(client, monkeypatch, buyer):
    client.force_login(buyer)
    session = client.session
    session["oidc_link"] = True
    session.save()
    claims = {"sub": "linked", "email": buyer.email, "email_verified": True}
    monkeypatch.setattr("storefront.views.oidc_client", lambda: FakeOIDCClient(claims))
    assert client.get("/auth/oidc/callback/").status_code == 302
    assert OIDCIdentity.objects.filter(user=buyer, subject="linked").exists()
