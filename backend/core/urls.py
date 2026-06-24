from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from shared.urls import contact_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth
    path("api/v1/auth/", include("apps.accounts.urls")),
    # Admin-only
    path("api/v1/admin/", include("apps.customers.urls_admin")),
    path("api/v1/admin/", include("apps.audit.urls")),
    # Client-facing (customers domain: me, invoices, metrics, invitations)
    path("api/v1/client/", include("apps.customers.urls_client")),
    # Client-facing (licenses — owned by subscriptions app)
    path("api/v1/client/licenses/", include("apps.subscriptions.urls_licenses")),
    # Client-facing (subscriptions — list, detail, change-plan, validate-license)
    path("api/v1/client/subscriptions/", include("apps.subscriptions.urls_client")),
    # Client-facing (api-keys — owned by licensing app)
    path("api/v1/client/api-keys/", include("apps.licensing.urls_client")),
    # Client-facing (in-app notifications)
    path("api/v1/client/notifications/", include("apps.notifications.urls_client")),
    # Public invitation accept (no auth required)
    path("api/v1/invitations/", include("apps.customers.urls_invitations")),
    # Billing (admin metrics — under /admin/ to match other admin routes)
    path("api/v1/admin/billing/", include("apps.billing.urls")),
    # Licensing (public validate-key only)
    path("api/v1/licensing/", include("apps.licensing.urls")),
    # Subscriptions + products (admin)
    path("api/v1/admin/", include("apps.subscriptions.urls_admin")),
    path("api/v1/admin/products/", include("apps.products.urls")),
    # Products (public — catalog only)
    path("api/v1/products/", include("apps.products.urls_public")),
    # Webhooks
    path("api/v1/webhooks/", include("apps.billing.urls_webhooks")),
    # Health
    path("health/", include("shared.urls")),
    # Contact form (public)
    path("api/v1/", include(contact_urlpatterns)),
    # OpenAPI schema + docs (apenas fora de produção ou com flag)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # CMS — public service pages
    path("api/v1/cms/", include("apps.cms.urls")),
    # CMS — admin revalidation
    path("api/v1/admin/cms/", include("apps.cms.urls_admin")),
]

# Serve /media/ in all environments — Cloudflare caches it at the edge in production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
