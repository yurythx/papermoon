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
