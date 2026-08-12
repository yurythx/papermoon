"""Integration tests for the Blog API endpoints (public + admin)."""

import io
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image as PILImage

from apps.blog.models import BlogPost


def _make_image_upload(name: str = "photo.png", fmt: str = "PNG") -> SimpleUploadedFile:
    buf = io.BytesIO()
    PILImage.new("RGB", (40, 30), color=(100, 150, 200)).save(buf, format=fmt)
    content_type = "image/png" if fmt == "PNG" else "image/jpeg"
    return SimpleUploadedFile(name, buf.getvalue(), content_type=content_type)


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

    def test_reading_time_is_computed_from_body_word_count(self, api_client, admin_user):
        # 400 palavras / 200 wpm = 2 min — sem precisar expor o body em si na listagem.
        _make_post(
            admin_user,
            status=BlogPost.Status.PUBLISHED,
            slug="longo",
            body=" ".join(["palavra"] * 400),
        )
        _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="curto", body="Só isso.")

        resp = api_client.get("/api/v1/blog/")
        by_slug = {row["slug"]: row["reading_time"] for row in resp.json()["data"]["results"]}
        assert by_slug["longo"] == 2
        assert by_slug["curto"] == 1  # mínimo de 1 minuto mesmo pra posts curtíssimos


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


class TestBlogBodyImageUpload:
    def test_admin_uploads_body_image(self, admin_client, admin_user):
        post = _make_post(admin_user, slug="post-com-imagem")
        resp = admin_client.post(
            f"/api/v1/admin/blog/{post.id}/body-image/",
            {"image": _make_image_upload()},
            format="multipart",
        )
        assert resp.status_code == 201
        image_url = resp.json()["data"]["image_url"]
        assert image_url
        assert post.slug in image_url
        assert image_url.endswith(".webp")  # convertida, igual à capa

    def test_missing_file_returns_400(self, admin_client, admin_user):
        post = _make_post(admin_user, slug="sem-arquivo")
        resp = admin_client.post(
            f"/api/v1/admin/blog/{post.id}/body-image/", {}, format="multipart"
        )
        assert resp.status_code == 400

    def test_non_image_file_rejected(self, admin_client, admin_user):
        post = _make_post(admin_user, slug="arquivo-invalido")
        bogus = SimpleUploadedFile(
            "not-an-image.png", b"isso nao e uma imagem", content_type="image/png"
        )
        resp = admin_client.post(
            f"/api/v1/admin/blog/{post.id}/body-image/", {"image": bogus}, format="multipart"
        )
        assert resp.status_code == 400

    def test_unknown_post_returns_404(self, admin_client):
        resp = admin_client.post(
            "/api/v1/admin/blog/00000000-0000-0000-0000-000000000000/body-image/",
            {"image": _make_image_upload()},
            format="multipart",
        )
        assert resp.status_code == 404

    def test_non_admin_cannot_upload(self, customer_client, admin_user):
        post = _make_post(admin_user, slug="sem-permissao")
        resp = customer_client.post(
            f"/api/v1/admin/blog/{post.id}/body-image/",
            {"image": _make_image_upload()},
            format="multipart",
        )
        assert resp.status_code == 403


class TestBlogTags:
    def test_admin_creates_post_with_tags(self, admin_client):
        resp = admin_client.post(
            "/api/v1/admin/blog/",
            {
                "title": "Post com tags",
                "slug": "post-com-tags",
                "excerpt": "x",
                "body": "",
                "tag_names": ["Zabbix", "Monitoramento"],
            },
            format="json",
        )
        assert resp.status_code == 201
        names = {t["name"] for t in resp.json()["data"]["tags"]}
        assert names == {"Zabbix", "Monitoramento"}

    def test_admin_updates_tags_reuses_existing_tag_by_slug(self, admin_client, admin_user):
        post = _make_post(admin_user, slug="post-tag-update")
        first = admin_client.patch(
            f"/api/v1/admin/blog/{post.id}/", {"tag_names": ["Backup"]}, format="json"
        )
        assert first.status_code == 200
        from apps.blog.models import Tag

        assert Tag.objects.filter(slug="backup").count() == 1

        # "backup" de novo (case diferente) não deve criar uma segunda tag
        second_post = _make_post(admin_user, slug="post-tag-update-2")
        second = admin_client.patch(
            f"/api/v1/admin/blog/{second_post.id}/", {"tag_names": ["backup"]}, format="json"
        )
        assert second.status_code == 200
        assert Tag.objects.filter(slug="backup").count() == 1

    def test_admin_clears_tags_with_empty_list(self, admin_client, admin_user):
        post = _make_post(admin_user, slug="post-tag-clear")
        admin_client.patch(f"/api/v1/admin/blog/{post.id}/", {"tag_names": ["x"]}, format="json")
        resp = admin_client.patch(
            f"/api/v1/admin/blog/{post.id}/", {"tag_names": []}, format="json"
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["tags"] == []

    def test_public_list_includes_tags(self, api_client, admin_user):
        post = _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="publicado-com-tag")
        from apps.blog.models import Tag

        tag = Tag.objects.create(name="GLPI", slug="glpi")
        post.tags.add(tag)

        resp = api_client.get("/api/v1/blog/")
        row = resp.json()["data"]["results"][0]
        assert row["tags"] == [{"name": "GLPI", "slug": "glpi"}]

    def test_public_list_filters_by_tag_slug(self, api_client, admin_user):
        from apps.blog.models import Tag

        glpi = Tag.objects.create(name="GLPI", slug="glpi")
        zabbix = Tag.objects.create(name="Zabbix", slug="zabbix")
        post_glpi = _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="sobre-glpi")
        post_glpi.tags.add(glpi)
        post_zabbix = _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="sobre-zabbix")
        post_zabbix.tags.add(zabbix)

        resp = api_client.get("/api/v1/blog/?tag=glpi")
        results = resp.json()["data"]["results"]
        assert len(results) == 1
        assert results[0]["slug"] == "sobre-glpi"

    def test_unknown_tag_slug_returns_empty_list(self, api_client, admin_user):
        _make_post(admin_user, status=BlogPost.Status.PUBLISHED, slug="publicado")
        resp = api_client.get("/api/v1/blog/?tag=nao-existe")
        assert resp.json()["data"]["results"] == []


class TestBlogRevalidationSignals:
    """Sem isso, despublicar ou excluir um post publicado deixa a URL antiga
    no ar: fetchBlogPost no frontend não tem ISR (cache: "no-store", ver
    lib/blog.ts) especificamente porque revalidateTag/revalidatePath não
    invalidam de forma confiável uma rota que passa a chamar notFound() — a
    garantia real de que o Next é avisado da mudança é essa task disparada
    pelo signal, tanto no save quanto no delete."""

    def test_save_triggers_revalidation_task(self, admin_user, db):
        with patch("apps.blog.tasks.revalidate_blog_post.delay") as mock_delay:
            post = _make_post(admin_user, slug="dispara-no-save")
        mock_delay.assert_called_once_with(post.slug)

    def test_delete_triggers_revalidation_task(self, admin_user, db):
        post = _make_post(admin_user, slug="dispara-no-delete")
        with patch("apps.blog.tasks.revalidate_blog_post.delay") as mock_delay:
            post.delete()
        mock_delay.assert_called_once_with("dispara-no-delete")
