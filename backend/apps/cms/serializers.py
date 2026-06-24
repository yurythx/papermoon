from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from apps.cms.models import (
    ServiceFAQ,
    ServiceFeatureGroup,
    ServiceFeatureItem,
    ServiceImage,
    ServicePage,
    ServiceResponsibility,
    ServiceStep,
)
from shared.public_urls import build_public_media_url


class ServiceStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStep
        fields = ["number", "title", "description", "order"]


class ServiceFeatureItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFeatureItem
        fields = ["text", "order"]


class ServiceFeatureGroupSerializer(serializers.ModelSerializer):
    items = ServiceFeatureItemSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceFeatureGroup
        fields = ["title", "items", "order"]


class ServiceFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFAQ
        fields = ["question", "answer", "order"]


class ServiceImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ServiceImage
        fields = ["url", "alt", "caption", "order"]

    def get_url(self, obj: ServiceImage) -> str | None:
        request = self.context.get("request")
        return build_public_media_url(obj.file.url if obj.file else None, request=request)


class ServiceImageAdminSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ServiceImage
        fields = ["id", "url", "alt", "caption", "order"]

    def get_url(self, obj: ServiceImage) -> str | None:
        request = self.context.get("request")
        return build_public_media_url(obj.file.url if obj.file else None, request=request)


class ServicePageSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(source="product.slug", read_only=True)
    hero_image_url = serializers.SerializerMethodField()
    papermoon_does = serializers.SerializerMethodField()
    client_does = serializers.SerializerMethodField()
    steps = ServiceStepSerializer(many=True, read_only=True)
    feature_groups = ServiceFeatureGroupSerializer(many=True, read_only=True)
    faqs = ServiceFAQSerializer(many=True, read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)

    class Meta:
        model = ServicePage
        fields = [
            "slug",
            "hero_image_url",
            "hero_image_alt",
            "tagline",
            "description",
            "meta_title",
            "meta_description",
            "papermoon_does",
            "client_does",
            "steps",
            "feature_groups",
            "faqs",
            "images",
            "updated_at",
        ]

    def get_hero_image_url(self, obj: ServicePage) -> str | None:
        request = self.context.get("request")
        return build_public_media_url(obj.hero_image.url if obj.hero_image else None, request=request)

    def get_papermoon_does(self, obj: ServicePage) -> list[str]:
        return [
            r.text for r in obj.responsibilities.all() if r.side == ServiceResponsibility.Side.PAPERMOON
        ]

    def get_client_does(self, obj: ServicePage) -> list[str]:
        return [r.text for r in obj.responsibilities.all() if r.side == "client"]


class ServiceSlugSerializer(serializers.Serializer):
    slug = serializers.CharField()


# ── Admin serializers (writable nested) ──────────────────────────────────────


class ServiceResponsibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceResponsibility
        fields = ["side", "text", "order"]


class ServiceStepWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStep
        fields = ["number", "title", "description", "order"]


class ServiceFeatureItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFeatureItem
        fields = ["text", "order"]


class ServiceFeatureGroupWriteSerializer(serializers.ModelSerializer):
    items = ServiceFeatureItemWriteSerializer(many=True, default=list)

    class Meta:
        model = ServiceFeatureGroup
        fields = ["title", "order", "items"]


class ServiceFAQWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFAQ
        fields = ["question", "answer", "order"]


class ServicePageAdminSerializer(serializers.ModelSerializer):
    """Read + write serializer for the backoffice CMS editor."""

    slug = serializers.CharField(source="product.slug", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    hero_image_url = serializers.SerializerMethodField()
    responsibilities = ServiceResponsibilitySerializer(many=True, default=list)
    steps = ServiceStepWriteSerializer(many=True, default=list)
    feature_groups = ServiceFeatureGroupWriteSerializer(many=True, default=list)
    faqs = ServiceFAQWriteSerializer(many=True, default=list)
    images = ServiceImageSerializer(many=True, read_only=True)

    class Meta:
        model = ServicePage
        fields = [
            "slug",
            "product_name",
            "hero_image_url",
            "hero_image_alt",
            "tagline",
            "description",
            "meta_title",
            "meta_description",
            "responsibilities",
            "steps",
            "feature_groups",
            "faqs",
            "images",
            "updated_at",
        ]
        read_only_fields = ["slug", "product_name", "hero_image_url", "images", "updated_at"]

    def get_hero_image_url(self, obj: ServicePage) -> str | None:
        request = self.context.get("request")
        return build_public_media_url(obj.hero_image.url if obj.hero_image else None, request=request)

    @transaction.atomic
    def update(self, instance: ServicePage, validated_data: dict) -> ServicePage:
        responsibilities_data = validated_data.pop("responsibilities", None)
        steps_data = validated_data.pop("steps", None)
        feature_groups_data = validated_data.pop("feature_groups", None)
        faqs_data = validated_data.pop("faqs", None)

        # Update scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Replace nested collections when provided
        if responsibilities_data is not None:
            instance.responsibilities.all().delete()
            for r in responsibilities_data:
                ServiceResponsibility.objects.create(page=instance, **r)

        if steps_data is not None:
            instance.steps.all().delete()
            for s in steps_data:
                ServiceStep.objects.create(page=instance, **s)

        if faqs_data is not None:
            instance.faqs.all().delete()
            for f in faqs_data:
                ServiceFAQ.objects.create(page=instance, **f)

        if feature_groups_data is not None:
            instance.feature_groups.all().delete()
            for g in feature_groups_data:
                items_data = g.pop("items", [])
                group = ServiceFeatureGroup.objects.create(page=instance, **g)
                for item in items_data:
                    ServiceFeatureItem.objects.create(group=group, **item)

        return instance


class ServicePageAdminListSerializer(serializers.Serializer):
    """Lightweight list row — product + CMS page status."""

    slug = serializers.CharField()
    product_name = serializers.CharField()
    has_page = serializers.BooleanField()
    updated_at = serializers.DateTimeField(allow_null=True)
