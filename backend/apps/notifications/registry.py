from collections.abc import Callable

# Handler signature: (payload: dict, event_id: str) -> None
# event_id is the OutboxEvent.id as string — handlers may use it as idempotency key.
HandlerFn = Callable[[dict, str], None]

_REGISTRY: dict[str, list[HandlerFn]] = {}


def register(event_type: str) -> Callable:
    """Decorator that registers a handler for a given OutboxEvent event_type."""

    def decorator(fn: HandlerFn) -> HandlerFn:
        _REGISTRY.setdefault(event_type, []).append(fn)
        return fn

    return decorator


def get_handlers(event_type: str) -> list[HandlerFn]:
    return list(_REGISTRY.get(event_type, []))


def registered_event_types() -> list[str]:
    return list(_REGISTRY.keys())
