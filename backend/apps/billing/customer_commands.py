"""
Commands that synchronize Customer records with the Asaas billing gateway.
Separated from billing/commands.py to keep invoice commands focused.
"""

import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class ProvisionAsaasCustomerCommand:
    """
    Creates (or retrieves) the customer in Asaas and persists asaas_customer_id.
    Idempotent: skips if asaas_customer_id is already set.
    Called by the customer.created OutboxEvent handler.
    """

    def execute(self, customer_id: UUID) -> str:
        from django.conf import settings

        from apps.billing.gateway.asaas_adapter import AsaasGateway
        from apps.customers.models import Customer

        if not getattr(settings, "ASAAS_API_KEY", ""):
            logger.warning(
                "ProvisionAsaasCustomerCommand skipped — ASAAS_API_KEY not set customer_id=%s",
                customer_id,
            )
            return ""

        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            logger.error("ProvisionAsaasCustomerCommand not found id=%s", customer_id)
            return ""

        if customer.asaas_customer_id:
            return customer.asaas_customer_id  # Idempotent

        gateway = AsaasGateway()
        try:
            asaas_id = gateway.create_customer(customer)
        except Exception as exc:
            logger.error(
                "ProvisionAsaasCustomerCommand gateway error customer_id=%s error=%s",
                customer_id,
                exc,
            )
            raise

        customer.asaas_customer_id = asaas_id
        customer.save(update_fields=["asaas_customer_id"])
        logger.info(
            "ProvisionAsaasCustomerCommand ok customer_id=%s asaas_id=%s",
            customer_id,
            asaas_id,
        )
        return asaas_id
