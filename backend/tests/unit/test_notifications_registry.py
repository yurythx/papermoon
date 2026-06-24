"""Unit tests for the notification handler registry."""

import pytest

from apps.notifications.registry import _REGISTRY, get_handlers, register


@pytest.fixture(autouse=True)
def clean_registry():
    """Isolate tests — save and restore the registry around each test."""
    snapshot = {k: list(v) for k, v in _REGISTRY.items()}
    yield
    _REGISTRY.clear()
    _REGISTRY.update(snapshot)


class TestRegisterDecorator:
    def test_registers_handler_for_event_type(self):
        @register("test.event")
        def my_handler(payload, event_id):
            pass

        assert my_handler in get_handlers("test.event")

    def test_multiple_handlers_for_same_event(self):
        @register("multi.event")
        def handler_a(payload, event_id):
            pass

        @register("multi.event")
        def handler_b(payload, event_id):
            pass

        handlers = get_handlers("multi.event")
        assert handler_a in handlers
        assert handler_b in handlers
        assert len(handlers) == 2

    def test_returns_empty_list_for_unknown_event(self):
        assert get_handlers("non.existent.event") == []

    def test_register_returns_original_function(self):
        @register("identity.event")
        def my_fn(payload, event_id):
            return "result"

        assert my_fn("payload", "id") == "result"

    def test_handlers_for_different_events_are_isolated(self):
        @register("event.a")
        def handler_a(payload, event_id):
            pass

        @register("event.b")
        def handler_b(payload, event_id):
            pass

        assert handler_a not in get_handlers("event.b")
        assert handler_b not in get_handlers("event.a")


class TestGetHandlers:
    def test_returns_copy_not_reference(self):
        @register("copy.test")
        def h(p, e):
            pass

        result = get_handlers("copy.test")
        result.clear()
        # Original registry must be unchanged
        assert len(get_handlers("copy.test")) == 1


class TestHandlerRegistration:
    """Verify that all business-critical events have at least one handler registered.
    These tests catch missing @register() calls after adding new event types.
    """

    REQUIRED_EVENTS = [
        "customer.created",
        "customer.suspended",
        "customer.reactivated",
        "customer.cancelled",
        "payment.processed",
        "payment.failed",
        "subscription.created",
        "subscription.renewed",
        "subscription.cancelled",
        "subscription.suspended",
        "subscription.expired",
        "subscription.grace_period",
        "subscription.expiring_soon",
        "subscription.plan_changed",
        "invitation.created",
        "quota.warning",
    ]

    def test_all_required_events_have_handlers(self):
        for event_type in self.REQUIRED_EVENTS:
            handlers = get_handlers(event_type)
            assert handlers, f"No handler registered for '{event_type}'"
