from abc import ABC, abstractmethod


class AbstractProvisioner(ABC):
    service_key: str

    @abstractmethod
    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        """Provision the service. Returns external_id."""

    @abstractmethod
    def suspend(self, external_id: str, customer_id: str) -> None:
        """Suspend access without deleting data."""

    @abstractmethod
    def reactivate(self, external_id: str, customer_id: str) -> None:
        """Reactivate a previously suspended access."""

    @abstractmethod
    def deprovision(self, external_id: str, customer_id: str) -> None:
        """Permanently remove the service for this customer."""
