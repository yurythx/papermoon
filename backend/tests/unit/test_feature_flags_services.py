"""Unit tests for apps.flags.services — real DB (fixture `db`), sem mock:
a lógica é toda queryset, não vale a pena isolar do ORM aqui."""

import pytest

from apps.flags.models import FeatureFlag
from apps.flags.services import is_enabled, list_enabled_keys


@pytest.fixture
def other_customer(db):
    from apps.customers.models import Customer

    return Customer.objects.create(company_name="Outra Empresa", document="11.111.111/0001-11")


class TestListEnabledKeys:
    def test_no_flags_returns_empty(self, db):
        assert list_enabled_keys(None) == []

    def test_global_flag_included_even_without_customer(self, db):
        FeatureFlag.objects.create(key="global_one", name="Global", enabled_globally=True)
        assert list_enabled_keys(None) == ["global_one"]

    def test_customer_specific_flag_not_included_for_other_customer(
        self, db, customer, other_customer
    ):
        flag = FeatureFlag.objects.create(key="beta_widget", name="Beta widget")
        flag.enabled_customers.add(customer)

        assert list_enabled_keys(customer.id) == ["beta_widget"]
        assert list_enabled_keys(other_customer.id) == []

    def test_global_and_customer_specific_combined_without_duplicates(self, db, customer):
        FeatureFlag.objects.create(key="global_one", name="Global", enabled_globally=True)
        beta = FeatureFlag.objects.create(key="beta_widget", name="Beta widget")
        beta.enabled_customers.add(customer)
        # Marcado como global E individualmente pro customer — não deve duplicar.
        both = FeatureFlag.objects.create(key="both_ways", name="Both", enabled_globally=True)
        both.enabled_customers.add(customer)

        keys = list_enabled_keys(customer.id)
        assert sorted(keys) == ["beta_widget", "both_ways", "global_one"]
        assert len(keys) == len(set(keys))

    def test_disabled_flag_never_appears(self, db, customer):
        FeatureFlag.objects.create(key="off", name="Off")
        assert list_enabled_keys(customer.id) == []


class TestIsEnabled:
    def test_unknown_key_is_false(self, db):
        assert is_enabled("does-not-exist", None) is False

    def test_global_flag_true_regardless_of_customer(self, db, customer):
        FeatureFlag.objects.create(key="global_one", name="Global", enabled_globally=True)
        assert is_enabled("global_one", None) is True
        assert is_enabled("global_one", customer.id) is True

    def test_customer_specific_flag(self, db, customer, other_customer):
        flag = FeatureFlag.objects.create(key="beta_widget", name="Beta widget")
        flag.enabled_customers.add(customer)

        assert is_enabled("beta_widget", customer.id) is True
        assert is_enabled("beta_widget", other_customer.id) is False
        assert is_enabled("beta_widget", None) is False
