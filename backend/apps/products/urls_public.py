from django.urls import path

from apps.products.views import ActiveServiceSlugsView, ProductCatalogView

urlpatterns = [
    path("catalog/", ProductCatalogView.as_view(), name="product-catalog"),
    path("active-slugs/", ActiveServiceSlugsView.as_view(), name="product-active-slugs"),
]
