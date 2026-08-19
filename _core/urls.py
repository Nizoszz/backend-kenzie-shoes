"""
URL configuration for _core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny, IsAdminUser

docs_permissions = [AllowAny] if settings.DEBUG else [IsAdminUser]

urlpatterns = [
    path("", include("storefront.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("users.urls")),
    path("api/", include("cart.urls")),
    path("api/", include("products.urls")),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=docs_permissions),
        name="schema",
    ),
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(
            url_name="schema", permission_classes=docs_permissions
        ),
    ),
]
