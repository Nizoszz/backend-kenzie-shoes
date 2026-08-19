from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Product
from .permissions import IsAdminAndSellerCreateUpdatedDestroy
from .serializers import ProductSerializer


class ProductPaginator(PageNumberPagination):
    page_size = 10


class ProductView(ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminAndSellerCreateUpdatedDestroy]
    serializer_class = ProductSerializer
    pagination_class = ProductPaginator

    def get_queryset(self):
        queryset = Product.objects.all()
        name = self.request.query_params.get("name", None)
        category = self.request.query_params.get("category", None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if category:
            queryset = queryset.filter(category__icontains=category)

        return queryset

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)


class ProductDetailView(RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminAndSellerCreateUpdatedDestroy]

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
