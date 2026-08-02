from django.apps import AppConfig


class SharedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shared"

    def ready(self) -> None:
        # AppConfig.ready() roda depois que o Django termina de carregar settings E
        # popular o app registry — o único ponto seguro pra instrumentar (Django,
        # Celery, psycopg2, Redis, requests). Chamar isso de dentro de
        # core/settings/base.py (como uma primeira versão fazia) reentra no
        # carregamento do próprio módulo de settings — DjangoInstrumentor precisa
        # mexer em settings.MIDDLEWARE, então falha silenciosamente nesse ponto em
        # vez de instrumentar de verdade. Ver docs/backend/observability.md.
        from django.conf import settings

        if not settings.OTEL_ENABLED:
            return

        from shared.tracing import setup_celery_tracing, setup_tracing

        setup_tracing(
            service_name=settings.OTEL_SERVICE_NAME,
            otlp_endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        )
        setup_celery_tracing()
