from django.urls import path

from cart.views import ProductCartView

from .views import ProductDetailView, ProductView

urlpatterns = [
    path("products/", ProductView.as_view()),
    path("products/<int:pk>/", ProductDetailView.as_view()),
    path("products/<int:pk>/cart/", ProductCartView.as_view()),
]
