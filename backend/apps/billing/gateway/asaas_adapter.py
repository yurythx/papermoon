import logging

from django.conf import settings
import requests

from apps.billing.gateway.interfaces import AbstractPaymentGateway

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.asaas.com/v3"


class AsaasGateway(AbstractPaymentGateway):
    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "access_token": settings.ASAAS_API_KEY,
                "Content-Type": "application/json",
            }
        )

    def create_customer(self, customer) -> str:
        """Provision customer in Asaas and return their Asaas customer ID."""
        payload = {
            "name": customer.company_name,
            "cpfCnpj": customer.document.replace(".", "").replace("/", "").replace("-", ""),
        }
        response = self._session.post(f"{_BASE_URL}/customers", json=payload)
        response.raise_for_status()
        return response.json()["id"]

    def create_charge(
        self,
        customer,
        invoice,
        billing_type: str = "BOLETO",
    ) -> dict:
        """
        Creates a payment charge in Asaas.

        billing_type: "BOLETO", "PIX" or "CREDIT_CARD".
        Defaults to BOLETO for backward-compatibility.
        """
        asaas_customer_id = customer.asaas_customer_id
        if not asaas_customer_id:
            raise ValueError(
                f"Customer {customer.id} has no asaas_customer_id. "
                "Provision the customer in Asaas first."
            )
        payload = {
            "customer": asaas_customer_id,
            "billingType": billing_type,
            "value": float(invoice.amount),
            "dueDate": str(invoice.due_date),
            "description": invoice.description or f"Fatura {invoice.id}",
        }
        response = self._session.post(f"{_BASE_URL}/payments", json=payload)
        response.raise_for_status()
        return response.json()

    def create_pix_charge(self, customer, invoice) -> dict:
        return self.create_charge(customer, invoice, billing_type="PIX")

    def get_charge_status(self, asaas_id: str) -> str:
        response = self._session.get(f"{_BASE_URL}/payments/{asaas_id}")
        response.raise_for_status()
        return response.json().get("status", "")

    def cancel_charge(self, asaas_id: str) -> bool:
        response = self._session.delete(f"{_BASE_URL}/payments/{asaas_id}")
        return response.status_code == 200
