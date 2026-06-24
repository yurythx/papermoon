from apps.support.client import ChatwootClient


class ProvisionCustomerCommand:
    def __init__(self, customer_id: str) -> None:
        self._customer_id = customer_id

    def execute(self) -> None:
        client = ChatwootClient()
        client.provision_customer(self._customer_id)


class SuspendAccessCommand:
    def __init__(self, customer_id: str) -> None:
        self._customer_id = customer_id

    def execute(self) -> None:
        client = ChatwootClient()
        client.suspend_agents(self._customer_id)


class ReactivateAccessCommand:
    def __init__(self, customer_id: str) -> None:
        self._customer_id = customer_id

    def execute(self) -> None:
        client = ChatwootClient()
        client.reactivate_agents(self._customer_id)
