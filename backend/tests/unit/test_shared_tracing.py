"""
Unit tests for shared/tracing.py.

Doesn't spin up a real OTLP exporter/collector — only exercises the OpenTelemetry
API surface (TracerProvider + InMemorySpanExporter), which is always available
regardless of OTEL_ENABLED. See docs/backend/observability.md.
"""

from shared.tracing import current_trace_context


class TestCurrentTraceContext:
    def test_returns_empty_strings_when_no_span_is_active(self):
        # Default global tracer provider (no SDK configured) — get_current_span()
        # returns an invalid/non-recording span in this state.
        trace_id, span_id = current_trace_context()
        assert trace_id == ""
        assert span_id == ""

    def test_returns_hex_ids_when_a_span_is_active(self):
        from opentelemetry.sdk.trace import TracerProvider

        provider = TracerProvider()
        tracer = provider.get_tracer(__name__)

        with tracer.start_as_current_span("test-span"):
            trace_id, span_id = current_trace_context()

        assert len(trace_id) == 32
        assert len(span_id) == 16
        # Valid hex, and not the all-zero "invalid" sentinel value.
        assert int(trace_id, 16) != 0
        assert int(span_id, 16) != 0

    def test_never_raises_even_if_internals_misbehave(self, monkeypatch):
        import opentelemetry.trace as otel_trace

        def _boom():
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(otel_trace, "get_current_span", _boom)
        assert current_trace_context() == ("", "")
