from django.urls import path

from apps.products.views import (
    PricingDetailView,
    PricingListCreateView,
    ProductDetailView,
    ProductListCreateView,
    ServiceComponentListCreateView,
)

urlpatterns = [
    path("", ProductListCreateView.as_view(), name="product-list"),
    path("<str:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path(
        "<str:product_pk>/components/",
        ServiceComponentListCreateView.as_view(),
        name="product-components",
    ),
    path("<str:product_pk>/pricings/", PricingListCreateView.as_view(), name="product-pricings"),
    path(
        "<str:product_pk>/pricings/<str:pricing_pk>/",
        PricingDetailView.as_view(),
        name="product-pricing-detail",
    ),
]
