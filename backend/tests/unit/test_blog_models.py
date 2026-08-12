"""Unit tests for apps/blog/models.py::BlogPost.mark_published."""

from django.utils import timezone
import pytest

from apps.blog.models import BlogPost


def _make_customer_user():
    from apps.accounts.models import CustomUser

    return CustomUser.objects.create_user(
        username="autor", email="autor@papermoon.com", password="x"
    )


@pytest.mark.django_db
class TestMarkPublished:
    def test_sets_published_at_when_publishing_for_the_first_time(self):
        author = _make_customer_user()
        post = BlogPost.objects.create(
            title="T",
            slug="t",
            excerpt="e",
            body="b",
            author=author,
            status=BlogPost.Status.PUBLISHED,
        )
        assert post.published_at is None

        post.mark_published()

        assert post.published_at is not None

    def test_does_not_overwrite_existing_published_at(self):
        author = _make_customer_user()
        original = timezone.now() - timezone.timedelta(days=5)
        post = BlogPost.objects.create(
            title="T",
            slug="t2",
            excerpt="e",
            body="b",
            author=author,
            status=BlogPost.Status.PUBLISHED,
            published_at=original,
        )

        post.mark_published()

        assert post.published_at == original

    def test_noop_while_still_draft(self):
        author = _make_customer_user()
        post = BlogPost.objects.create(title="T", slug="t3", excerpt="e", body="b", author=author)

        post.mark_published()

        assert post.published_at is None
