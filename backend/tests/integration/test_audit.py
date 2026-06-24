import pytest

from apps.audit.models import AuditLog


def _make_log(admin_user, resource_type="customer", action="created"):
    return AuditLog.objects.create(
        user=admin_user,
        action=action,
        resource_type=resource_type,
        resource_id="some-uuid",
        changes={},
    )


@pytest.mark.django_db
class TestAuditLogEndpoint:
    def test_admin_can_list_audit_logs(self, admin_client, admin_user):
        _make_log(admin_user)
        resp = admin_client.get("/api/v1/admin/audit-logs/")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_non_admin_cannot_access_audit_logs(self, customer_client):
        resp = customer_client.get("/api/v1/admin/audit-logs/")
        assert resp.status_code == 403

    def test_unauthenticated_cannot_access_audit_logs(self, api_client):
        resp = api_client.get("/api/v1/admin/audit-logs/")
        assert resp.status_code == 401

    def test_audit_log_is_read_only(self, admin_client):
        resp = admin_client.post("/api/v1/admin/audit-logs/", {}, format="json")
        assert resp.status_code == 405

    def test_filter_by_resource_type(self, admin_client, admin_user):
        _make_log(admin_user, resource_type="customer")
        _make_log(admin_user, resource_type="invoice")
        resp = admin_client.get("/api/v1/admin/audit-logs/?resource_type=customer")
        results = resp.json()["data"]["results"]
        assert all(r["resource_type"] == "customer" for r in results)

    def test_filter_by_action(self, admin_client, admin_user):
        _make_log(admin_user, action="created")
        _make_log(admin_user, action="suspended")
        resp = admin_client.get("/api/v1/admin/audit-logs/?action=created")
        results = resp.json()["data"]["results"]
        assert all(r["action"] == "created" for r in results)

    def test_response_includes_user_email(self, admin_client, admin_user):
        _make_log(admin_user)
        resp = admin_client.get("/api/v1/admin/audit-logs/")
        results = resp.json()["data"]["results"]
        assert results[0]["user_email"] == admin_user.email
