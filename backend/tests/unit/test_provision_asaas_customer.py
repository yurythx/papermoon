"""Unit tests for ProvisionAsaasCustomerCommand."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from apps.billing.customer_commands import ProvisionAsaasCustomerCommand
from apps.customers.models import Customer


def _make_customer(asaas_customer_id: str = "") -> Customer:
    return Customer.objects.create(
        company_name="Provision Corp",
        document=f"{uuid4().int % 10**14:014d}"[:18],
        asaas_customer_id=asaas_customer_id,
    )


@pytest.mark.django_db
class TestProvisionAsaasCustomerCommand:
    # The import of AsaasGateway happens inside execute() via
    # `from apps.billing.gateway.asaas_adapter import AsaasGateway`
    # so the correct patch target is the source module, not customer_commands.
    _GATEWAY_PATH = "apps.billing.gateway.asaas_adapter.AsaasGateway"
    _SETTINGS_PATH = "apps.billing.customer_commands.settings"

    def _patch_gateway(self, gateway):
        return patch(self._GATEWAY_PATH, return_value=gateway)

    def _patch_api_key(self, key="fake-key"):
        """Ensure ASAAS_API_KEY is set so the command doesn't skip."""
        return patch.object(
            __import__("django.conf", fromlist=["settings"]).settings,
            "ASAAS_API_KEY",
            key,
        )

    def test_calls_gateway_create_customer(self):
        from unittest.mock import patch

        customer = _make_customer()
        gateway = MagicMock()
        gateway.create_customer.return_value = "cus_asaas_001"

        with (
            patch(self._GATEWAY_PATH, return_value=gateway),
            patch("django.conf.settings.ASAAS_API_KEY", "fake-key"),
        ):
            result = ProvisionAsaasCustomerCommand().execute(customer.id)

        gateway.create_customer.assert_called_once_with(customer)
        assert result == "cus_asaas_001"

    def test_persists_asaas_customer_id(self):
        from unittest.mock import patch

        customer = _make_customer()
        gateway = MagicMock()
        gateway.create_customer.return_value = "cus_asaas_002"

        with (
            patch(self._GATEWAY_PATH, return_value=gateway),
            patch("django.conf.settings.ASAAS_API_KEY", "fake-key"),
        ):
            ProvisionAsaasCustomerCommand().execute(customer.id)

        customer.refresh_from_db()
        assert customer.asaas_customer_id == "cus_asaas_002"

    def test_idempotent_when_asaas_id_already_set(self):
        from unittest.mock import patch

        customer = _make_customer(asaas_customer_id="existing_id")
        gateway = MagicMock()

        with (
            patch(self._GATEWAY_PATH, return_value=gateway),
            patch("django.conf.settings.ASAAS_API_KEY", "fake-key"),
        ):
            result = ProvisionAsaasCustomerCommand().execute(customer.id)

        gateway.create_customer.assert_not_called()
        assert result == "existing_id"

    def test_returns_empty_string_for_missing_customer(self):
        from unittest.mock import patch

        gateway = MagicMock()

        with (
            patch(self._GATEWAY_PATH, return_value=gateway),
            patch("django.conf.settings.ASAAS_API_KEY", "fake-key"),
        ):
            result = ProvisionAsaasCustomerCommand().execute(uuid4())

        gateway.create_customer.assert_not_called()
        assert result == ""

    def test_propagates_gateway_exception(self):
        from unittest.mock import patch

        customer = _make_customer()
        gateway = MagicMock()
        gateway.create_customer.side_effect = RuntimeError("Asaas down")

        with (
            patch(self._GATEWAY_PATH, return_value=gateway),
            patch("django.conf.settings.ASAAS_API_KEY", "fake-key"),
            pytest.raises(RuntimeError, match="Asaas down"),
        ):
            ProvisionAsaasCustomerCommand().execute(customer.id)

    def test_does_not_overwrite_existing_asaas_id_on_retry(self):
        from unittest.mock import patch

        customer = _make_customer(asaas_customer_id="original_id")
        gateway = MagicMock()
        gateway.create_customer.return_value = "should_not_be_used"

        with (
            patch(self._GATEWAY_PATH, return_value=gateway),
            patch("django.conf.settings.ASAAS_API_KEY", "fake-key"),
        ):
            result = ProvisionAsaasCustomerCommand().execute(customer.id)

        customer.refresh_from_db()
        assert customer.asaas_customer_id == "original_id"
        assert result == "original_id"
