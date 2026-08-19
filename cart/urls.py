from django.urls import path

from .views import ProductCartDetailView

urlpatterns = [
    path("cart/<int:pk>/", ProductCartDetailView.as_view()),
]
