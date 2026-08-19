import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from cart.models import Cart
from products.models import Product

from .models import UserOrder

security_logger = logging.getLogger("commerce.security")


class CheckoutError(Exception):
    pass


@transaction.atomic
def checkout_cart(user):
    items = list(
        Cart.objects.select_related("product").select_for_update().filter(user=user)
    )
    if not items:
        raise CheckoutError("Carrinho está vazio")

    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(
            id__in=[item.product_id for item in items]
        )
    }
    for item in items:
        if item.quantities > products[item.product_id].stock:
            raise CheckoutError(f"Estoque insuficiente para {item.product.name}")

    orders = []
    for item in items:
        product = products[item.product_id]
        product.stock -= item.quantities
        product.save(update_fields=("stock",))
        orders.append(UserOrder.objects.create(products=product, user=user))

    Cart.objects.filter(user=user).delete()

    def send_confirmation():
        details = ", ".join(f"#{order.id} - {order.products.name}" for order in orders)
        try:
            send_mail(
                "Confirmação de Ordem de Compra",
                f"Prezado(a) {user.first_name}, sua compra foi realizada: {details}.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception:
            security_logger.exception(
                "order_confirmation_email_failed user_id=%s order_ids=%s",
                user.id,
                [order.id for order in orders],
            )

    security_logger.info(
        "checkout_completed user_id=%s order_ids=%s",
        user.id,
        [order.id for order in orders],
    )
    transaction.on_commit(send_confirmation)
    return orders
