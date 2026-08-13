"""Integration tests for the Feature Flags admin API."""

from apps.flags.models import FeatureFlag


class TestFeatureFlagListCreate:
    def test_non_admin_cannot_list(self, customer_client):
        resp = customer_client.get("/api/v1/admin/feature-flags/")
        assert resp.status_code == 403

    def test_unauthenticated_cannot_list(self, api_client, db):
        resp = api_client.get("/api/v1/admin/feature-flags/")
        assert resp.status_code == 401

    def test_admin_lists_flags(self, admin_client, db):
        FeatureFlag.objects.create(key="flag_a", name="Flag A")
        FeatureFlag.objects.create(key="flag_b", name="Flag B", enabled_globally=True)

        resp = admin_client.get("/api/v1/admin/feature-flags/")
        assert resp.status_code == 200
        keys = {row["key"] for row in resp.json()["data"]}
        assert keys == {"flag_a", "flag_b"}

    def test_admin_creates_flag_disabled_by_default(self, admin_client, db):
        resp = admin_client.post(
            "/api/v1/admin/feature-flags/",
            {"key": "new_dashboard_widget", "name": "Novo widget do dashboard"},
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["key"] == "new_dashboard_widget"
        assert data["enabled_globally"] is False
        assert data["enabled_customers"] == []

    def test_create_duplicate_key_returns_400(self, admin_client, db):
        FeatureFlag.objects.create(key="dup", name="Dup")
        resp = admin_client.post(
            "/api/v1/admin/feature-flags/", {"key": "dup", "name": "Outra"}, format="json"
        )
        assert resp.status_code == 400

    def test_create_missing_required_field_returns_400(self, admin_client, db):
        resp = admin_client.post("/api/v1/admin/feature-flags/", {"key": "sem-nome"}, format="json")
        assert resp.status_code == 400


class TestFeatureFlagDetail:
    def test_get_unknown_id_returns_404(self, admin_client, db):
        resp = admin_client.get("/api/v1/admin/feature-flags/99999/")
        assert resp.status_code == 404

    def test_patch_toggles_global(self, admin_client, db):
        flag = FeatureFlag.objects.create(key="toggle_me", name="Toggle")
        resp = admin_client.patch(
            f"/api/v1/admin/feature-flags/{flag.id}/", {"enabled_globally": True}, format="json"
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["enabled_globally"] is True
        flag.refresh_from_db()
        assert flag.enabled_globally is True

    def test_patch_sets_enabled_customers(self, admin_client, customer, db):
        flag = FeatureFlag.objects.create(key="beta_widget", name="Beta")
        resp = admin_client.patch(
            f"/api/v1/admin/feature-flags/{flag.id}/",
            {"enabled_customer_ids": [str(customer.id)]},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["enabled_customers"]) == 1
        assert data["enabled_customers"][0]["company_name"] == customer.company_name
        assert flag.enabled_customers.filter(pk=customer.id).exists()

    def test_delete_removes_flag(self, admin_client, db):
        flag = FeatureFlag.objects.create(key="to_delete", name="Delete me")
        resp = admin_client.delete(f"/api/v1/admin/feature-flags/{flag.id}/")
        assert resp.status_code == 204
        assert not FeatureFlag.objects.filter(pk=flag.id).exists()

    def test_non_admin_cannot_patch(self, customer_client, db):
        flag = FeatureFlag.objects.create(key="protected", name="Protected")
        resp = customer_client.patch(
            f"/api/v1/admin/feature-flags/{flag.id}/", {"enabled_globally": True}, format="json"
        )
        assert resp.status_code == 403
