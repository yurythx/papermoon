"""Support OutboxEvent handlers — registered in NotificationsConfig.ready()."""

from apps.notifications.registry import register


@register("customer.created")
def provision_chatwoot(payload: dict, event_id: str) -> None:
    from apps.support.commands import ProvisionCustomerCommand

    ProvisionCustomerCommand(payload["customer_id"]).execute()


@register("customer.suspended")
def suspend_chatwoot(payload: dict, event_id: str) -> None:
    from apps.support.commands import SuspendAccessCommand

    SuspendAccessCommand(payload["customer_id"]).execute()


@register("customer.reactivated")
def reactivate_chatwoot(payload: dict, event_id: str) -> None:
    from apps.support.commands import ReactivateAccessCommand

    ReactivateAccessCommand(payload["customer_id"]).execute()
