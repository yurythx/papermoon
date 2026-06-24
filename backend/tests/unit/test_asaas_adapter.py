"""Unit tests for apps/billing/gateway/asaas_adapter.py.

All HTTP calls are mocked so no real network access is needed.
"""

import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


def _make_gateway():
    with patch("apps.billing.gateway.asaas_adapter.requests.Session") as MockSession:
        session_instance = MagicMock()
        MockSession.return_value = session_instance
        from apps.billing.gateway.asaas_adapter import AsaasGateway

        gw = AsaasGateway()
        gw._session = session_instance
        return gw, session_instance


# ---------------------------------------------------------------------------
# create_customer
# ---------------------------------------------------------------------------


def test_create_customer_returns_asaas_id():
    gw, session = _make_gateway()
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "cus_abc123"}
    session.post.return_value = mock_response

    customer = MagicMock()
    customer.company_name = "Acme Ltda"
    customer.document = "12.345.678/0001-90"

    result = gw.create_customer(customer)

    assert result == "cus_abc123"
    session.post.assert_called_once()
    call_kwargs = session.post.call_args
    payload = call_kwargs[1]["json"]
    assert payload["cpfCnpj"] == "12345678000190"
    mock_response.raise_for_status.assert_called_once()


def test_create_customer_strips_formatting_from_cnpj():
    gw, session = _make_gateway()
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "cus_xyz"}
    session.post.return_value = mock_response

    customer = MagicMock()
    customer.company_name = "Test Co"
    customer.document = "00.000.000/0001-00"

    gw.create_customer(customer)

    payload = session.post.call_args[1]["json"]
    assert "." not in payload["cpfCnpj"]
    assert "/" not in payload["cpfCnpj"]
    assert "-" not in payload["cpfCnpj"]


# ---------------------------------------------------------------------------
# create_charge
# ---------------------------------------------------------------------------


def test_create_charge_returns_response_json():
    gw, session = _make_gateway()
    expected = {"id": "pay_123", "status": "PENDING"}
    mock_response = MagicMock()
    mock_response.json.return_value = expected
    session.post.return_value = mock_response

    customer = MagicMock()
    customer.asaas_customer_id = "cus_abc123"

    invoice = MagicMock()
    invoice.amount = Decimal("199.00")
    invoice.due_date = datetime.date(2099, 12, 31)
    invoice.id = "inv-uuid-1234"

    result = gw.create_charge(customer, invoice)

    assert result == expected
    payload = session.post.call_args[1]["json"]
    assert payload["customer"] == "cus_abc123"
    assert payload["value"] == 199.0
    assert payload["dueDate"] == "2099-12-31"
    mock_response.raise_for_status.assert_called_once()


def test_create_charge_raises_when_no_asaas_customer_id():
    gw, session = _make_gateway()

    customer = MagicMock()
    customer.asaas_customer_id = None

    invoice = MagicMock()

    with pytest.raises(ValueError, match="asaas_customer_id"):
        gw.create_charge(customer, invoice)

    session.post.assert_not_called()


def test_create_charge_raises_when_asaas_customer_id_empty():
    gw, session = _make_gateway()

    customer = MagicMock()
    customer.asaas_customer_id = ""

    invoice = MagicMock()

    with pytest.raises(ValueError):
        gw.create_charge(customer, invoice)


# ---------------------------------------------------------------------------
# get_charge_status
# ---------------------------------------------------------------------------


def test_get_charge_status_returns_status_string():
    gw, session = _make_gateway()
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "pay_123", "status": "RECEIVED"}
    session.get.return_value = mock_response

    result = gw.get_charge_status("pay_123")

    assert result == "RECEIVED"
    session.get.assert_called_once()
    assert "pay_123" in session.get.call_args[0][0]
    mock_response.raise_for_status.assert_called_once()


def test_get_charge_status_returns_empty_string_when_missing():
    gw, session = _make_gateway()
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    session.get.return_value = mock_response

    result = gw.get_charge_status("pay_no_status")

    assert result == ""


# ---------------------------------------------------------------------------
# cancel_charge
# ---------------------------------------------------------------------------


def test_cancel_charge_returns_true_on_200():
    gw, session = _make_gateway()
    mock_response = MagicMock()
    mock_response.status_code = 200
    session.delete.return_value = mock_response

    assert gw.cancel_charge("pay_123") is True
    session.delete.assert_called_once()
    assert "pay_123" in session.delete.call_args[0][0]


def test_cancel_charge_returns_false_on_non_200():
    gw, session = _make_gateway()
    mock_response = MagicMock()
    mock_response.status_code = 404
    session.delete.return_value = mock_response

    assert gw.cancel_charge("pay_missing") is False
