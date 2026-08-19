from django.urls import path
from .views import UserView, UserDetailView
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView
from orders.views import OrderView, OrderDetailView, BuyOrderView, SellOrderView
from .views import LoginView

urlpatterns = [
    path("users/", UserView.as_view()),
    path("users/<int:pk>/", UserDetailView.as_view()),
    path("users/orders/", OrderView.as_view()),
    path("users/buyorders/", BuyOrderView.as_view()),
    path("users/sellorders/", SellOrderView.as_view()),
    path("users/orders/<int:pk>/", OrderDetailView.as_view()),
    path("users/login/", LoginView.as_view()),
    path("users/token/refresh/", TokenRefreshView.as_view()),
    path("users/logout/", TokenBlacklistView.as_view()),
]
