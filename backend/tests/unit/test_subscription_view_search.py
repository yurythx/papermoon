"""
Unit tests for list_subscriptions_admin() query function.

No DB required — patches Subscription.objects.
Verifies that search, status, customer_id and ordering filters are applied correctly.
"""

from unittest.mock import MagicMock, call, patch


def _make_queryset_chain():
    """Return a mock queryset that records filter/order_by calls."""
    final_qs = MagicMock()
    final_qs.count.return_value = 0
    final_qs.__getitem__ = MagicMock(return_value=[])

    qs = MagicMock()
    qs.select_related.return_value = qs
    qs.prefetch_related.return_value = qs
    qs.filter.return_value = qs
    qs.order_by.return_value = final_qs

    return qs, final_qs


def _call_query(**kwargs):
    from apps.subscriptions.queries import list_subscriptions_admin

    qs, _ = _make_queryset_chain()

    with patch("apps.subscriptions.queries.Subscription.objects", qs):
        list_subscriptions_admin(**kwargs)

    return qs


class TestListSubscriptionsAdminQuery:
    def test_search_applies_icontains_filter(self):
        qs = _call_query(search="Acme")
        qs.filter.assert_called_once_with(customer__company_name__icontains="Acme")

    def test_whitespace_search_skips_filter(self):
        qs = _call_query(search="   ")
        qs.filter.assert_not_called()

    def test_no_search_skips_filter(self):
        qs = _call_query()
        qs.filter.assert_not_called()

    def test_search_and_status_both_filter(self):
        qs = _call_query(search="Beta", status="active")
        calls = qs.filter.call_args_list
        assert call(customer__company_name__icontains="Beta") in calls
        assert call(status="active") in calls

    def test_customer_id_filter(self):
        import uuid

        cid = str(uuid.uuid4())
        qs = _call_query(customer_id=cid)
        qs.filter.assert_called_once_with(customer_id=cid)

    def test_unknown_ordering_falls_back_to_default(self):
        qs, _ = _make_queryset_chain()
        from apps.subscriptions.queries import list_subscriptions_admin

        with patch("apps.subscriptions.queries.Subscription.objects", qs):
            list_subscriptions_admin(ordering="malicious_field; DROP TABLE")

        qs.order_by.assert_called_once_with("-created_at")
