from django.urls import path

from apps.products.views import ProductCatalogView

urlpatterns = [
    path("catalog/", ProductCatalogView.as_view(), name="product-catalog"),
]
