"""Integration tests for the Blog API endpoints (public + admin)."""

from django.utils import timezone

from apps.blog.models import BlogPost


def _make_post(author, status=BlogPost.Status.DRAFT, slug="post-1", **overrides):
    defaults = {
        "title": "Como configurar SSO com Keycloak",
        "slug": slug,
        "excerpt": "Um guia rápido de boas práticas.",
        "body": "# Título\n\nCorpo em **markdown**.",
        "author": author,
        "status": status,
    }
    defaults.update(overrides)
    post = BlogPost.objects.create(**defaults)
    if status == BlogPost.Status.PUBLISHED and post.published_at is None:
        post.published_at = timezone.now()
        post.save(update_fields=["published_at"])
    return post


class TestBlogPublicList:
    def test_returns_empty_list_when_no_posts(self, api_client, db):
        resp = api_client.get("/api/v1/blog/")
        assert resp.status_code == 200
        assert resp.json()["data"]["results"] == []

    def test_only_published_posts_are_listed(self, api_client, admin_user):
        _make_post(admin_user, status=BlogPost.Status.DRAFT, slug="rascunho")
        _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="publicado")

        resp = api_client.get("/api/v1/blog/")
        results = resp.json()["data"]["results"]
        assert len(results) == 1
        assert results[0]["slug"] == "publicado"

    def test_list_row_has_no_body(self, api_client, admin_user):
        _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="publicado")
        resp = api_client.get("/api/v1/blog/")
        assert "body" not in resp.json()["data"]["results"][0]


class TestBlogPublicDetail:
    def test_published_post_returns_200_with_body(self, api_client, admin_user):
        _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="publicado")
        resp = api_client.get("/api/v1/blog/publicado/")
        assert resp.status_code == 200
        assert resp.json()["data"]["body"].startswith("# Título")

    def test_draft_post_returns_404(self, api_client, admin_user):
        _make_post(admin_user, status=BlogPost.Status.DRAFT, slug="rascunho")
        resp = api_client.get("/api/v1/blog/rascunho/")
        assert resp.status_code == 404

    def test_nonexistent_slug_returns_404(self, api_client, db):
        resp = api_client.get("/api/v1/blog/nao-existe/")
        assert resp.status_code == 404


class TestBlogAdminListCreate:
    def test_non_admin_cannot_list(self, customer_client):
        resp = customer_client.get("/api/v1/admin/blog/")
        assert resp.status_code == 403

    def test_unauthenticated_cannot_list(self, api_client, db):
        resp = api_client.get("/api/v1/admin/blog/")
        assert resp.status_code == 401

    def test_admin_lists_all_statuses(self, admin_client, admin_user):
        _make_post(admin_user, status=BlogPost.Status.DRAFT, slug="rascunho")
        _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="publicado")

        resp = admin_client.get("/api/v1/admin/blog/")
        assert resp.status_code == 200
        assert resp.json()["data"]["count"] == 2

    def test_admin_filters_by_status(self, admin_client, admin_user):
        _make_post(admin_user, status=BlogPost.Status.DRAFT, slug="rascunho")
        _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="publicado")

        resp = admin_client.get("/api/v1/admin/blog/?status=draft")
        results = resp.json()["data"]["results"]
        assert len(results) == 1
        assert results[0]["slug"] == "rascunho"

    def test_admin_creates_post_as_draft_authored_by_self(self, admin_client, admin_user):
        resp = admin_client.post(
            "/api/v1/admin/blog/",
            {
                "title": "Novo post",
                "slug": "novo-post",
                "excerpt": "Resumo.",
                "body": "Corpo.",
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "draft"
        assert data["author"] == admin_user.id
        assert data["published_at"] is None

    def test_admin_creates_post_with_empty_body(self, admin_client):
        # O modal de criação do backoffice manda body="" de propósito — o corpo
        # é escrito depois, no editor completo. body precisa aceitar blank.
        resp = admin_client.post(
            "/api/v1/admin/blog/",
            {"title": "Rascunho vazio", "slug": "rascunho-vazio", "excerpt": "Resumo.", "body": ""},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["body"] == ""

    def test_create_missing_required_field_returns_400(self, admin_client):
        resp = admin_client.post("/api/v1/admin/blog/", {"title": "Sem slug"}, format="json")
        assert resp.status_code == 400


class TestBlogAdminDetail:
    def test_get_returns_post(self, admin_client, admin_user):
        post = _make_post(admin_user, slug="post-detalhe")
        resp = admin_client.get(f"/api/v1/admin/blog/{post.id}/")
        assert resp.status_code == 200
        assert resp.json()["data"]["slug"] == "post-detalhe"

    def test_get_unknown_id_returns_404(self, admin_client):
        resp = admin_client.get("/api/v1/admin/blog/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == 404

    def test_patch_publishes_and_sets_published_at(self, admin_client, admin_user):
        post = _make_post(admin_user, status=BlogPost.Status.DRAFT, slug="a-publicar")
        assert post.published_at is None

        resp = admin_client.patch(
            f"/api/v1/admin/blog/{post.id}/", {"status": "published"}, format="json"
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "published"
        assert data["published_at"] is not None

    def test_republish_does_not_reset_published_at(self, admin_client, admin_user):
        post = _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="ja-publicado")
        before = admin_client.get(f"/api/v1/admin/blog/{post.id}/").json()["data"]["published_at"]

        resp = admin_client.patch(
            f"/api/v1/admin/blog/{post.id}/", {"title": "Título ajustado"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["published_at"] == before

    def test_delete_removes_post(self, admin_client, admin_user):
        post = _make_post(admin_user, slug="a-remover")
        resp = admin_client.delete(f"/api/v1/admin/blog/{post.id}/")
        assert resp.status_code == 204
        assert not BlogPost.objects.filter(pk=post.id).exists()

    def test_author_field_is_not_writable_by_client(self, admin_client, admin_user, regular_user):
        post = _make_post(admin_user, slug="autor-fixo")
        resp = admin_client.patch(
            f"/api/v1/admin/blog/{post.id}/",
            {"author": str(regular_user.id)},
            format="json",
        )
        assert resp.status_code == 200
        post.refresh_from_db()
        assert post.author_id == admin_user.id
