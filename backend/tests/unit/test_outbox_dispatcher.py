"""Unit tests for the centralised OutboxEvent dispatcher."""

import pytest


@pytest.mark.django_db
class TestProcessOutboxEvents:
    def _create_event(self, event_type, payload=None):
        from shared.models import OutboxEvent

        return OutboxEvent.objects.create(
            event_type=event_type,
            payload=payload or {},
        )

    def test_marks_event_processed_after_handler_runs(self):
        from apps.notifications.registry import _REGISTRY, register
        from apps.notifications.tasks import process_outbox_events

        calls = []

        @register("test.processed")
        def h(payload, event_id):
            calls.append(event_id)

        try:
            event = self._create_event("test.processed", {"key": "value"})
            process_outbox_events()

            event.refresh_from_db()
            assert event.processed is True
            assert event.processed_at is not None
            assert str(event.id) in calls
        finally:
            _REGISTRY.get("test.processed", []).clear()

    def test_event_with_no_handler_is_marked_processed(self):
        from apps.notifications.tasks import process_outbox_events
        from shared.models import OutboxEvent

        event = OutboxEvent.objects.create(
            event_type="orphan.event.xyz",
            payload={},
        )
        process_outbox_events()

        event.refresh_from_db()
        assert event.processed is True

    def test_failed_handler_increments_retry_count(self):
        from apps.notifications.registry import _REGISTRY, register
        from apps.notifications.tasks import process_outbox_events

        @register("test.failing")
        def bad_handler(payload, event_id):
            raise RuntimeError("handler error")

        try:
            event = self._create_event("test.failing")
            process_outbox_events()

            event.refresh_from_db()
            assert event.processed is False
            assert event.retry_count == 1
            assert "handler error" in event.last_error
        finally:
            _REGISTRY.get("test.failing", []).clear()

    def test_event_at_max_retries_is_marked_failed(self):
        from apps.notifications.registry import _REGISTRY, register
        from apps.notifications.tasks import _MAX_RETRIES, process_outbox_events
        from shared.models import OutboxEvent

        @register("test.maxretry")
        def always_fails(payload, event_id):
            raise RuntimeError("permanent failure")

        try:
            event = OutboxEvent.objects.create(
                event_type="test.maxretry",
                payload={},
                retry_count=_MAX_RETRIES - 1,
            )
            process_outbox_events()

            event.refresh_from_db()
            assert event.retry_count == _MAX_RETRIES
            assert event.failed_at is not None
        finally:
            _REGISTRY.get("test.maxretry", []).clear()

    def test_already_processed_events_are_skipped(self):
        from django.utils import timezone

        from apps.notifications.registry import _REGISTRY, register
        from apps.notifications.tasks import process_outbox_events

        calls = []

        @register("test.skip")
        def h(payload, event_id):
            calls.append(event_id)

        try:
            from shared.models import OutboxEvent

            OutboxEvent.objects.create(
                event_type="test.skip",
                payload={},
                processed=True,
                processed_at=timezone.now(),
            )
            process_outbox_events()
            assert calls == []
        finally:
            _REGISTRY.get("test.skip", []).clear()

    def test_handler_receives_correct_payload_and_event_id(self):
        from apps.notifications.registry import _REGISTRY, register
        from apps.notifications.tasks import process_outbox_events

        received = {}

        @register("test.payload")
        def capture(payload, event_id):
            received["payload"] = payload
            received["event_id"] = event_id

        try:
            event = self._create_event("test.payload", {"foo": "bar"})
            process_outbox_events()

            assert received["payload"] == {"foo": "bar"}
            assert received["event_id"] == str(event.id)
        finally:
            _REGISTRY.get("test.payload", []).clear()


@pytest.mark.django_db
class TestOutboxEventTraceCapture:
    """OutboxEvent.save() auto-captures the active OTel span — see shared/models.py."""

    def test_no_active_span_leaves_trace_fields_empty(self):
        from shared.models import OutboxEvent

        event = OutboxEvent.objects.create(event_type="test.no_span", payload={})
        assert event.trace_id == ""
        assert event.span_id == ""

    def test_creating_inside_an_active_span_captures_trace_and_span_id(self):
        from opentelemetry.sdk.trace import TracerProvider

        from shared.models import OutboxEvent

        tracer = TracerProvider().get_tracer(__name__)
        with tracer.start_as_current_span("http-request-span"):
            event = OutboxEvent.objects.create(event_type="test.with_span", payload={})

        assert len(event.trace_id) == 32
        assert len(event.span_id) == 16

    def test_trace_id_is_not_overwritten_on_subsequent_saves(self):
        from opentelemetry.sdk.trace import TracerProvider

        from shared.models import OutboxEvent

        tracer = TracerProvider().get_tracer(__name__)
        with tracer.start_as_current_span("http-request-span"):
            event = OutboxEvent.objects.create(event_type="test.resave", payload={})
        original_trace_id = event.trace_id

        with tracer.start_as_current_span("a-different-later-span"):
            event.processed = True
            event.save()

        assert event.trace_id == original_trace_id


class TestOutboxSpanLinks:
    """_outbox_span_links() — see apps/notifications/tasks.py."""

    def _fake_event(self, trace_id="", span_id=""):
        from types import SimpleNamespace

        return SimpleNamespace(trace_id=trace_id, span_id=span_id)

    def test_no_trace_id_returns_empty_links(self):
        from apps.notifications.tasks import _outbox_span_links

        assert _outbox_span_links(self._fake_event()) == []

    def test_valid_ids_produce_one_link(self):
        from apps.notifications.tasks import _outbox_span_links

        links = _outbox_span_links(self._fake_event(trace_id="a" * 32, span_id="b" * 16))
        assert len(links) == 1
        assert links[0].context.trace_id == int("a" * 32, 16)
        assert links[0].context.span_id == int("b" * 16, 16)
        assert links[0].context.is_remote is True

    def test_malformed_hex_returns_empty_links_not_exception(self):
        from apps.notifications.tasks import _outbox_span_links

        assert (
            _outbox_span_links(self._fake_event(trace_id="not-hex", span_id="also-not-hex")) == []
        )
