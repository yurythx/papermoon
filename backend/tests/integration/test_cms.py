"""Integration tests for the CMS API endpoints."""

import pytest

from apps.cms.models import ServiceFAQ, ServicePage, ServiceResponsibility, ServiceStep
from apps.products.models import Product


@pytest.fixture
def product(db):
    return Product.objects.create(name="Zabbix Monitoring", slug="zabbix")


@pytest.fixture
def cms_page(db, product):
    page = ServicePage.objects.create(
        product=product,
        tagline="Visibilidade total da sua infra",
        description="Monitore servidores, redes e VMs.",
        meta_title="Zabbix — PaperMoon",
        meta_description="Monitoramento com Zabbix gerenciado.",
    )
    ServiceStep.objects.create(
        page=page, number="01", title="Levantamento", description="Mapeamos.", order=0
    )
    ServiceFAQ.objects.create(page=page, question="Quanto custa?", answer="Consulte.", order=0)
    ServiceResponsibility.objects.create(page=page, side="papermoon", text="Instalamos.", order=0)
    ServiceResponsibility.objects.create(page=page, side="client", text="Fornece acesso.", order=0)
    return page


class TestCMSServiceSlugList:
    def test_returns_empty_list_when_no_pages(self, api_client, db):
        resp = api_client.get("/api/v1/cms/services/")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_returns_slug_when_page_exists(self, api_client, cms_page):
        resp = api_client.get("/api/v1/cms/services/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Returns a flat list of slug strings
        assert "zabbix" in data

    def test_no_auth_required(self, api_client, db):
        resp = api_client.get("/api/v1/cms/services/")
        assert resp.status_code == 200


class TestCMSServicePageDetail:
    def test_returns_404_when_no_page(self, api_client, db):
        resp = api_client.get("/api/v1/cms/services/nonexistent/")
        assert resp.status_code == 404

    def test_returns_page_data(self, api_client, cms_page):
        resp = api_client.get("/api/v1/cms/services/zabbix/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["slug"] == "zabbix"
        assert data["tagline"] == "Visibilidade total da sua infra"
        assert data["description"] == "Monitore servidores, redes e VMs."
        assert data["meta_title"] == "Zabbix — PaperMoon"

    def test_steps_serialized(self, api_client, cms_page):
        resp = api_client.get("/api/v1/cms/services/zabbix/")
        steps = resp.json()["data"]["steps"]
        assert len(steps) == 1
        assert steps[0]["number"] == "01"
        assert steps[0]["title"] == "Levantamento"

    def test_faqs_serialized(self, api_client, cms_page):
        resp = api_client.get("/api/v1/cms/services/zabbix/")
        faqs = resp.json()["data"]["faqs"]
        assert len(faqs) == 1
        assert faqs[0]["question"] == "Quanto custa?"

    def test_responsibilities_split_by_side(self, api_client, cms_page):
        resp = api_client.get("/api/v1/cms/services/zabbix/")
        data = resp.json()["data"]
        assert "Instalamos." in data["papermoon_does"]
        assert "Fornece acesso." in data["client_does"]

    def test_no_auth_required(self, api_client, cms_page):
        resp = api_client.get("/api/v1/cms/services/zabbix/")
        assert resp.status_code == 200

    def test_hero_image_url_null_when_no_image(self, api_client, cms_page):
        resp = api_client.get("/api/v1/cms/services/zabbix/")
        assert resp.json()["data"]["hero_image_url"] is None

    def test_images_empty_when_none(self, api_client, cms_page):
        resp = api_client.get("/api/v1/cms/services/zabbix/")
        assert resp.json()["data"]["images"] == []


class TestCMSRevalidateEndpoint:
    def test_non_admin_gets_403(self, customer_client):
        resp = customer_client.post("/api/v1/admin/cms/revalidate/zabbix/")
        assert resp.status_code == 403

    def test_unauthenticated_gets_401(self, api_client):
        resp = api_client.post("/api/v1/admin/cms/revalidate/zabbix/")
        assert resp.status_code == 401

    def test_admin_triggers_revalidation(self, admin_client, cms_page, mocker):
        mock_task = mocker.patch("apps.cms.views.revalidate_service_page")
        resp = admin_client.post("/api/v1/admin/cms/revalidate/zabbix/")
        assert resp.status_code == 200
        mock_task.delay.assert_called_once_with("zabbix")

    def test_admin_revalidate_returns_slug_in_body(self, admin_client, db, mocker):
        # The endpoint fires the task async — it doesn't validate whether the slug exists
        mocker.patch("apps.cms.views.revalidate_service_page")
        resp = admin_client.post("/api/v1/admin/cms/revalidate/any-slug/")
        assert resp.status_code == 200
        assert resp.json()["data"]["slug"] == "any-slug"
