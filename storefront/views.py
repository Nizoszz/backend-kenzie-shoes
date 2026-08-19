import logging
from urllib.parse import urlencode

from authlib.integrations.base_client.errors import OAuthError
from requests.exceptions import RequestException
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from addresses.models import Address
from cart.models import Cart
from orders.models import OrderStatus, UserOrder
from orders.services import CheckoutError, checkout_cart
from products.models import Category, Product
from users.models import OIDCIdentity, PartnerApplication, User

from .forms import (
    AddressForm,
    CartQuantityForm,
    LoginForm,
    PartnerApplicationForm,
    ProductForm,
    ProfileForm,
    RegistrationForm,
)
from .oidc import oidc_client

logger = logging.getLogger(__name__)


def _safe_next(request, default="storefront:shop"):
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return reverse(default)


def _cart_context(user):
    if not user.is_authenticated:
        return {"cart_items": [], "cart_count": 0, "cart_total": 0}
    items = list(Cart.objects.select_related("product").filter(user=user))
    return {
        "cart_items": items,
        "cart_count": len(items),
        "cart_total": sum(item.product.value * item.quantities for item in items),
    }


def _oidc_context():
    enabled = bool(settings.OIDC_SERVER_METADATA_URL and settings.OIDC_CLIENT_ID)
    return {
        "oidc_enabled": enabled,
        "oidc_provider_name": settings.OIDC_PROVIDER_NAME,
    }


@require_GET
def home(request):
    featured = Product.objects.filter(stock__gt=0).order_by("-id")[:4]
    return render(request, "storefront/home.html", {"featured": featured, **_cart_context(request.user)})


@require_GET
def shop(request):
    products = Product.objects.select_related("user").all()
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category:
        products = products.filter(category=category)
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    context = {"page_obj": page, "query": query, "selected_category": category, "categories": Category.choices}
    context.update(_cart_context(request.user))
    return render(request, "storefront/shop.html", context)


class StorefrontLoginView(LoginView):
    template_name = "storefront/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_oidc_context())
        return context


def register(request):
    if request.user.is_authenticated:
        return redirect("storefront:shop")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Conta criada com sucesso.")
        return redirect("storefront:shop")
    return render(request, "storefront/register.html", {"form": form, **_oidc_context()})


@require_POST
def logout(request):
    auth_logout(request)
    messages.success(request, "Sessão encerrada.")
    return redirect("storefront:home")


@login_required
@never_cache
def account(request):
    profile_form = ProfileForm(request.POST or None, instance=request.user, prefix="profile")
    address_form = AddressForm(request.POST or None, instance=request.user.address, prefix="address")
    if request.method == "POST" and profile_form.is_valid() and address_form.is_valid():
        with transaction.atomic():
            address = address_form.save()
            user = profile_form.save(commit=False)
            user.address = address
            user.save()
        messages.success(request, "Perfil atualizado.")
        return redirect(_safe_next(request, "storefront:account"))
    return render(
        request,
        "storefront/account.html",
        {
            "profile_form": profile_form,
            "address_form": address_form,
            **_oidc_context(),
            **_cart_context(request.user),
        },
    )


@login_required
@require_POST
def cart_add(request, product_id):
    if not request.user.profile_complete:
        messages.warning(request, "Complete seu endereço antes de usar o carrinho.")
        return redirect(f"{reverse('storefront:account')}?next={reverse('storefront:shop')}")
    product = get_object_or_404(Product, pk=product_id)
    form = CartQuantityForm(request.POST)
    if not form.is_valid() or form.cleaned_data["quantities"] > product.stock:
        messages.error(request, "Quantidade indisponível.")
    else:
        try:
            Cart.objects.create(user=request.user, product=product, quantities=form.cleaned_data["quantities"])
            messages.success(request, "Produto adicionado ao carrinho.")
        except IntegrityError:
            messages.warning(request, "Esse produto já está no seu carrinho.")
    return redirect(_safe_next(request))


@login_required
@never_cache
def cart_detail(request):
    return render(request, "storefront/cart.html", _cart_context(request.user))


@login_required
@require_POST
def cart_update(request, cart_id):
    item = get_object_or_404(Cart.objects.select_related("product"), pk=cart_id, user=request.user)
    form = CartQuantityForm(request.POST)
    if form.is_valid() and form.cleaned_data["quantities"] <= item.product.stock:
        item.quantities = form.cleaned_data["quantities"]
        item.save(update_fields=("quantities",))
        messages.success(request, "Quantidade atualizada.")
    else:
        messages.error(request, "Quantidade indisponível.")
    return redirect("storefront:cart")


@login_required
@require_POST
def cart_remove(request, cart_id):
    get_object_or_404(Cart, pk=cart_id, user=request.user).delete()
    messages.success(request, "Produto removido.")
    return redirect("storefront:cart")


@login_required
@require_POST
def checkout(request):
    if not request.user.profile_complete:
        messages.warning(request, "Complete seu endereço antes de finalizar o pedido.")
        return redirect("storefront:account")
    try:
        checkout_cart(request.user)
    except CheckoutError as error:
        messages.error(request, str(error))
        return redirect("storefront:cart")
    messages.success(request, "Pedido realizado com sucesso.")
    return redirect("storefront:orders")


@login_required
@never_cache
def orders(request):
    queryset = UserOrder.objects.select_related("products").filter(user=request.user).order_by("-buyed_at")
    return render(request, "storefront/orders.html", {"orders": queryset, **_cart_context(request.user)})


@login_required
@never_cache
def partner_apply(request):
    pending = PartnerApplication.objects.filter(user=request.user, status=PartnerApplication.Status.PENDING).first()
    form = PartnerApplicationForm(request.POST or None)
    if request.method == "POST":
        if request.user.is_seller:
            messages.info(request, "Sua conta já é vendedora.")
            return redirect("storefront:seller")
        if pending:
            messages.warning(request, "Você já possui uma solicitação pendente.")
        elif form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            messages.success(request, "Solicitação enviada para análise.")
            return redirect("storefront:partner_apply")
    return render(request, "storefront/partner_apply.html", {"form": form, "pending": pending, **_cart_context(request.user)})


def _require_seller(user):
    if not user.is_authenticated or not (user.is_seller or user.is_staff):
        raise PermissionDenied


@login_required
@never_cache
def seller_dashboard(request):
    _require_seller(request.user)
    products = Product.objects.filter(user=request.user)
    sales = UserOrder.objects.select_related("products", "user").filter(products__user=request.user).order_by("-buyed_at")
    return render(request, "storefront/seller.html", {"products": products, "sales": sales, "statuses": OrderStatus.choices, **_cart_context(request.user)})


@login_required
@never_cache
def seller_product_create(request):
    _require_seller(request.user)
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.user = request.user
        product.save()
        messages.success(request, "Produto cadastrado.")
        return redirect("storefront:seller")
    return render(request, "storefront/product_form.html", {"form": form, **_cart_context(request.user)})


@login_required
@require_POST
def seller_order_status(request, order_id):
    _require_seller(request.user)
    queryset = UserOrder.objects.all() if request.user.is_staff else UserOrder.objects.filter(products__user=request.user)
    order = get_object_or_404(queryset, pk=order_id)
    status = request.POST.get("status")
    if status not in OrderStatus.values:
        return HttpResponseBadRequest("Status inválido")
    order.status = status
    order.save(update_fields=("status",))
    messages.success(request, "Status atualizado.")
    return redirect("storefront:seller")


def oidc_login(request):
    client = oidc_client()
    if client is None:
        messages.error(request, "Login OIDC não está configurado.")
        return redirect("storefront:login")
    request.session["oidc_link"] = request.GET.get("link") == "1" and request.user.is_authenticated
    redirect_uri = settings.OIDC_REDIRECT_URI or request.build_absolute_uri(
        reverse("storefront:oidc_callback")
    )
    try:
        return client.authorize_redirect(request, redirect_uri)
    except (OAuthError, RequestException, ValueError) as error:
        messages.error(
            request,
            "Não foi possível acessar o provedor OIDC. Verifique metadata, client ID e redirect URI.",
        )
        logger.warning("OIDC authorization could not start: %s", error)
        return redirect("storefront:login")


def _unique_username(seed):
    base = "".join(character for character in seed if character.isalnum() or character in "._-")[:40] or "user"
    candidate = base
    counter = 1
    while User.objects.filter(username=candidate).exists():
        counter += 1
        candidate = f"{base[:44]}-{counter}"
    return candidate


def oidc_callback(request):
    client = oidc_client()
    if client is None:
        return redirect("storefront:login")
    try:
        token = client.authorize_access_token(request)
        claims = token["userinfo"]
    except (OAuthError, KeyError):
        messages.error(request, "Não foi possível validar a identidade externa.")
        return redirect("storefront:login")

    if claims.get("email_verified") is not True or not claims.get("sub") or not claims.get("email"):
        messages.error(request, "O provedor deve confirmar um e-mail verificado.")
        return redirect("storefront:login")

    provider = settings.OIDC_PROVIDER_NAME
    identity = OIDCIdentity.objects.select_related("user").filter(provider=provider, subject=claims["sub"]).first()
    linking = request.session.pop("oidc_link", False)
    if linking and request.user.is_authenticated:
        if identity and identity.user_id != request.user.id:
            messages.error(request, "Essa identidade já pertence a outra conta.")
        else:
            OIDCIdentity.objects.get_or_create(provider=provider, subject=claims["sub"], defaults={"user": request.user})
            messages.success(request, "Identidade externa vinculada.")
        return redirect("storefront:account")

    if identity:
        user = identity.user
    elif User.objects.filter(email__iexact=claims["email"]).exists():
        messages.error(request, "Já existe uma conta com esse e-mail. Entre localmente e vincule o provedor no perfil.")
        return redirect("storefront:login")
    else:
        user = User.objects.create(
            username=_unique_username(claims.get("preferred_username") or claims["email"].split("@")[0]),
            email=claims["email"],
            first_name=claims.get("given_name") or "Novo",
            last_name=claims.get("family_name") or "Usuário",
        )
        user.set_unusable_password()
        user.save(update_fields=("password",))
        OIDCIdentity.objects.create(provider=provider, subject=claims["sub"], user=user)

    auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    if not user.profile_complete:
        messages.info(request, "Complete seu endereço para continuar.")
        return redirect("storefront:account")
    return redirect("storefront:shop")
