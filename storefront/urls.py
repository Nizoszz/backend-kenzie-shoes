from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "storefront"

urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    path(
        "dashboard/",
        RedirectView.as_view(pattern_name="storefront:shop", permanent=False),
        name="dashboard",
    ),
    path("login/", views.StorefrontLoginView.as_view(), name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),
    path("account/", views.account, name="account"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/<int:cart_id>/update/", views.cart_update, name="cart_update"),
    path("cart/<int:cart_id>/remove/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.orders, name="orders"),
    path("partner/apply/", views.partner_apply, name="partner_apply"),
    path("seller/", views.seller_dashboard, name="seller"),
    path(
        "seller/products/new/",
        views.seller_product_create,
        name="seller_product_create",
    ),
    path(
        "seller/orders/<int:order_id>/status/",
        views.seller_order_status,
        name="seller_order_status",
    ),
    path("auth/oidc/login/", views.oidc_login, name="oidc_login"),
    path("auth/oidc/callback/", views.oidc_callback, name="oidc_callback"),
]
