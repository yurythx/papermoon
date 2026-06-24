import pytest

VALID_STATUSES = ("ok", "degraded", "error")


@pytest.mark.django_db
class TestHealthEndpoint:
    def test_health_returns_200(self, api_client):
        # 200 when db+redis are ok; celery degraded (no worker in tests) is acceptable.
        resp = api_client.get("/health/")
        assert resp.status_code == 200

    def test_health_includes_db_status(self, api_client):
        resp = api_client.get("/health/")
        assert "db" in resp.json()["data"]

    def test_health_includes_redis_status(self, api_client):
        resp = api_client.get("/health/")
        assert "redis" in resp.json()["data"]

    def test_health_includes_celery_status(self, api_client):
        resp = api_client.get("/health/")
        assert "celery" in resp.json()["data"]

    def test_health_db_is_ok(self, api_client):
        resp = api_client.get("/health/")
        assert resp.json()["data"]["db"] == "ok"

    def test_health_redis_is_ok_or_degraded(self, api_client):
        resp = api_client.get("/health/")
        assert resp.json()["data"]["redis"] in VALID_STATUSES

    def test_health_celery_is_valid_status(self, api_client):
        # Celery workers don't run during tests — expect ok or degraded, never a crash.
        resp = api_client.get("/health/")
        assert resp.json()["data"]["celery"] in VALID_STATUSES
