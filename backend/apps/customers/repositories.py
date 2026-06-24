from uuid import UUID

from django.db.models import QuerySet
from rest_framework.exceptions import NotFound

from apps.customers.interfaces import AbstractCustomerRepository
from apps.customers.models import Customer


class DjangoCustomerRepository(AbstractCustomerRepository):
    def get_by_id(self, customer_id: UUID) -> Customer:
        try:
            return Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist as exc:
            raise NotFound(f"Customer {customer_id} não encontrado.") from exc

    def get_any_by_id(self, customer_id: UUID) -> Customer:
        try:
            return Customer.all_objects.get(pk=customer_id)
        except Customer.DoesNotExist as exc:
            raise NotFound(f"Customer {customer_id} não encontrado.") from exc

    def get_all(self) -> QuerySet:
        return Customer.objects.all()

    def create(self, data: dict) -> Customer:
        return Customer.objects.create(**data)

    def update(self, customer_id: UUID, data: dict) -> Customer:
        customer = self.get_by_id(customer_id)
        for field, value in data.items():
            setattr(customer, field, value)
        customer.save()
        return customer

    def save(self, customer: Customer) -> Customer:
        customer.save()
        return customer
