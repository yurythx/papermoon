"""
Setup do OpenTelemetry — tracing distribuído para Django, Celery, Postgres, Redis
e chamadas HTTP de saída (os 19 `apps/provisioning/*` chamam Chatwoot, GLPI,
Zabbix etc. via `requests`). Ver docs/backend/observability.md.

Desativado por padrão (`OTEL_ENABLED=False`) — mesmo princípio de fallback usado
pelos provisioners quando faltam credenciais: sem tracing configurado, tudo aqui
vira no-op, nunca derruba a aplicação. Testes e CI não ativam por padrão.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_django_instrumented = False
_celery_instrumented = False


def setup_tracing(*, service_name: str, otlp_endpoint: str) -> None:
    """Instrumenta Django, psycopg2, Redis e requests. Idempotente — chamado uma
    vez por processo (web, worker ou beat) na carga das settings.

    Recebe os valores já resolvidos em vez de ler `django.conf.settings` — é
    chamado de dentro de core/settings/base.py, ainda em execução: reacessar o
    proxy de settings nesse ponto reentra no carregamento do módulo de settings
    (via core/__init__.py -> celery_app.py -> app.config_from_object) e quebra
    com AttributeError, porque a settings ainda não terminou de carregar.
    """
    global _django_instrumented
    if _django_instrumented:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        DjangoInstrumentor().instrument()
        Psycopg2Instrumentor().instrument()
        RedisInstrumentor().instrument()
        RequestsInstrumentor().instrument()

        _django_instrumented = True
        logger.info("OpenTelemetry ativado — service=%s export=%s", service_name, otlp_endpoint)
    except Exception:
        # Nunca derruba o processo por causa de observabilidade — loga e segue sem tracing.
        logger.exception("Falha ao inicializar OpenTelemetry — seguindo sem tracing.")


def setup_celery_tracing() -> None:
    """Chamado em core/celery_app.py (worker e beat), só quando OTEL_ENABLED —
    instrumenta o ciclo de vida das tasks do Celery, além do que setup_tracing()
    já cobre (chamado separadamente, ao carregar as settings)."""
    global _celery_instrumented
    if _celery_instrumented:
        return

    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor

        CeleryInstrumentor().instrument()
        _celery_instrumented = True
    except Exception:
        logger.exception("Falha ao instrumentar Celery — seguindo sem tracing de tasks.")


def current_trace_context() -> tuple[str, str]:
    """(trace_id, span_id) em hex do span ativo, ou ("", "") se não houver
    tracing ativo/span válido no momento da chamada. Usado por
    shared.models.OutboxEvent para correlacionar um evento ao request que o
    originou — ver apps/notifications/tasks.py para o lado do consumer."""
    try:
        from opentelemetry import trace

        span_context = trace.get_current_span().get_span_context()
        if not span_context.is_valid:
            return "", ""
        return format(span_context.trace_id, "032x"), format(span_context.span_id, "016x")
    except Exception:
        return "", ""
