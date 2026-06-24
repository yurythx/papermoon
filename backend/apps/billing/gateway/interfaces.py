from abc import ABC, abstractmethod


class AbstractPaymentGateway(ABC):
    @abstractmethod
    def create_customer(self, customer) -> str:
        """Provision customer in the gateway. Returns gateway customer ID."""

    @abstractmethod
    def create_charge(self, customer, invoice) -> dict: ...

    @abstractmethod
    def get_charge_status(self, asaas_id: str) -> str: ...

    @abstractmethod
    def cancel_charge(self, asaas_id: str) -> bool: ...
