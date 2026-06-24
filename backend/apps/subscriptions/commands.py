from __future__ import annotations

from datetime import timedelta
import decimal
import logging
from typing import TYPE_CHECKING
from uuid import UUID

from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from datetime import datetime

    from apps.subscriptions.models import Subscription

logger = logging.getLogger(__name__)


class CreateSubscriptionCommand:
    def execute(self, customer_id: UUID, product_id: UUID, pricing_id: UUID) -> Subscription:
        from apps.customers.models import Customer
        from apps.products.models import Pricing, Product
        from apps.subscriptions.models import License, ServiceAccess, Subscription
        from shared.models import OutboxEvent

        customer = Customer.objects.get(pk=customer_id)
        product = Product.objects.prefetch_related("components").get(pk=product_id)
        pricing = Pricing.objects.get(pk=pricing_id, product=product)

        now = timezone.now()
        expires_at = compute_expiry(now, pricing)
        is_trial = pricing.trial_days > 0

        with transaction.atomic():
            subscription = Subscription.objects.create(
                customer=customer,
                product=product,
                pricing=pricing,
                status=Subscription.Status.TRIAL if is_trial else Subscription.Status.ACTIVE,
                starts_at=now,
                expires_at=now + timedelta(days=pricing.trial_days) if is_trial else expires_at,
            )

            license_obj = License.objects.create(
                subscription=subscription,
                customer=customer,
                key=License.generate_key(),
                status=License.Status.ACTIVE,
                valid_from=now,
                valid_until=subscription.expires_at,
            )

            service_keys = []
            for component in product.components.all():
                ServiceAccess.objects.create(
                    license=license_obj,
                    service_key=component.service_key,
                    status=ServiceAccess.Status.PROVISIONING,
                    config=component.config,
                )
                service_keys.append(component.service_key)

            OutboxEvent.objects.create(
                event_type="subscription.created",
                payload={
                    "subscription_id": str(subscription.id),
                    "license_id": str(license_obj.id),
                    "customer_id": str(customer.id),
                    "product_slug": product.slug,
                    "service_keys": service_keys,
                },
            )

        return subscription


class RenewSubscriptionCommand:
    def execute(self, subscription_id: UUID) -> Subscription:
        from apps.subscriptions.models import License, ServiceAccess, Subscription
        from shared.models import OutboxEvent

        with transaction.atomic():
            subscription = Subscription.objects.select_for_update().get(pk=subscription_id)
            now = timezone.now()
            new_expiry = compute_expiry(now, subscription.pricing)

            subscription.expires_at = new_expiry
            subscription.status = Subscription.Status.ACTIVE
            subscription.save(update_fields=["expires_at", "status", "updated_at"])

            license_obj = subscription.license
            license_obj.valid_until = new_expiry
            license_obj.status = License.Status.ACTIVE
            license_obj.save(update_fields=["valid_until", "status"])

            license_obj.service_accesses.filter(status=ServiceAccess.Status.SUSPENDED).update(
                status=ServiceAccess.Status.ACTIVE, suspended_at=None
            )

            OutboxEvent.objects.create(
                event_type="subscription.renewed",
                payload={
                    "subscription_id": str(subscription.id),
                    "customer_id": str(subscription.customer_id),
                    "new_expiry": new_expiry.isoformat(),
                },
            )

        return subscription


class ReactivateSubscriptionCommand:
    """
    Client-side reactivation of a suspended subscription.
    Allowed transition: SUSPENDED → ACTIVE.
    Does NOT extend expires_at — keeps the original expiry so the billing cycle
    is preserved. Use RenewSubscriptionCommand for payment-confirmed renewal.
    """

    def execute(self, subscription_id: UUID) -> Subscription:
        from apps.subscriptions.models import License, ServiceAccess, Subscription
        from shared.models import OutboxEvent

        with transaction.atomic():
            subscription = Subscription.objects.select_for_update().get(pk=subscription_id)

            if subscription.status != Subscription.Status.SUSPENDED:
                raise ValueError(
                    f"Only suspended subscriptions can be reactivated. Current status: {subscription.status}"
                )

            subscription.transition_to(Subscription.Status.ACTIVE)

            license_obj = subscription.license
            license_obj.status = License.Status.ACTIVE
            license_obj.save(update_fields=["status"])

            license_obj.service_accesses.filter(status=ServiceAccess.Status.SUSPENDED).update(
                status=ServiceAccess.Status.ACTIVE, suspended_at=None
            )

            OutboxEvent.objects.create(
                event_type="subscription.renewed",
                payload={
                    "subscription_id": str(subscription.id),
                    "customer_id": str(subscription.customer_id),
                    "new_expiry": subscription.expires_at.isoformat(),
                },
            )

        return subscription


class SuspendSubscriptionCommand:
    def execute(self, subscription_id: UUID, reason: str = "") -> Subscription:
        from apps.subscriptions.models import License, ServiceAccess, Subscription
        from shared.models import OutboxEvent

        with transaction.atomic():
            subscription = Subscription.objects.select_for_update().get(pk=subscription_id)
            subscription.transition_to(Subscription.Status.SUSPENDED)

            license_obj = subscription.license
            license_obj.status = License.Status.SUSPENDED
            license_obj.save(update_fields=["status"])

            now = timezone.now()
            service_keys = list(license_obj.service_accesses.values_list("service_key", flat=True))
            license_obj.service_accesses.filter(status=ServiceAccess.Status.ACTIVE).update(
                status=ServiceAccess.Status.SUSPENDED, suspended_at=now
            )

            OutboxEvent.objects.create(
                event_type="subscription.suspended",
                payload={
                    "subscription_id": str(subscription.id),
                    "license_id": str(license_obj.id),
                    "customer_id": str(subscription.customer_id),
                    "service_keys": service_keys,
                    "reason": reason,
                },
            )

        return subscription


class ExpireSubscriptionCommand:
    """Called by Celery beat scan_expiring_subscriptions."""

    def execute(self, subscription_id: UUID) -> Subscription:
        from apps.subscriptions.models import License, ServiceAccess, Subscription
        from shared.models import OutboxEvent

        with transaction.atomic():
            subscription = Subscription.objects.select_for_update().get(pk=subscription_id)

            if subscription.status == Subscription.Status.ACTIVE:
                subscription.transition_to(Subscription.Status.GRACE_PERIOD)
                license_obj = subscription.license
                license_obj.status = License.Status.GRACE_PERIOD
                license_obj.save(update_fields=["status"])

                OutboxEvent.objects.create(
                    event_type="subscription.grace_period",
                    payload={
                        "subscription_id": str(subscription.id),
                        "customer_id": str(subscription.customer_id),
                        "expires_at": subscription.expires_at.isoformat(),
                    },
                )
            else:
                # Grace period ended — fully expire
                subscription.transition_to(Subscription.Status.EXPIRED)

                license_obj = subscription.license
                license_obj.status = License.Status.EXPIRED
                license_obj.save(update_fields=["status"])

                now = timezone.now()
                service_keys = list(
                    license_obj.service_accesses.values_list("service_key", flat=True)
                )
                license_obj.service_accesses.filter(
                    status__in=[
                        ServiceAccess.Status.ACTIVE,
                        ServiceAccess.Status.SUSPENDED,
                    ]
                ).update(status=ServiceAccess.Status.DEPROVISIONED, suspended_at=now)

                OutboxEvent.objects.create(
                    event_type="subscription.expired",
                    payload={
                        "subscription_id": str(subscription.id),
                        "license_id": str(license_obj.id),
                        "customer_id": str(subscription.customer_id),
                        "service_keys": service_keys,
                    },
                )

        return subscription


class CancelSubscriptionCommand:
    def execute(self, subscription_id: UUID, reason: str = "") -> Subscription:
        from apps.subscriptions.models import License, ServiceAccess, Subscription
        from shared.models import OutboxEvent

        with transaction.atomic():
            subscription = Subscription.objects.select_for_update().get(pk=subscription_id)
            subscription.transition_to(Subscription.Status.CANCELLED)

            license_obj = subscription.license
            license_obj.status = License.Status.REVOKED
            license_obj.revoked_at = timezone.now()
            license_obj.save(update_fields=["status", "revoked_at"])

            service_keys = list(license_obj.service_accesses.values_list("service_key", flat=True))
            license_obj.service_accesses.exclude(status=ServiceAccess.Status.DEPROVISIONED).update(
                status=ServiceAccess.Status.DEPROVISIONED,
                suspended_at=timezone.now(),
            )

            OutboxEvent.objects.create(
                event_type="subscription.cancelled",
                payload={
                    "subscription_id": str(subscription.id),
                    "license_id": str(license_obj.id),
                    "customer_id": str(subscription.customer_id),
                    "service_keys": service_keys,
                    "reason": reason,
                },
            )

        return subscription


class ChangeSubscriptionPlanCommand:
    """
    Upgrades or downgrades a subscription to a different Pricing within the same Product.

    Behaviour:
    - Cancels the current subscription (emits subscription.plan_changed).
    - Creates a new subscription with the new pricing (emits subscription.created).
    - Existing ServiceAccess records carry over — services keep running.
    - Quota limits are re-synced via the subscription.created handler.
    - On upgrade: creates a proration invoice for the unused days of the old plan.

    Both operations are wrapped in a single transaction.atomic() so the customer
    is never left without a subscription on DB failure.
    """

    def execute(self, subscription_id: UUID, new_pricing_id: UUID) -> Subscription:
        from apps.products.models import Pricing
        from apps.subscriptions.models import License, ServiceAccess, Subscription
        from shared.models import OutboxEvent

        with transaction.atomic():
            old_sub = Subscription.objects.select_for_update().get(pk=subscription_id)
            new_pricing = Pricing.objects.get(pk=new_pricing_id, product=old_sub.product)

            if new_pricing.id == old_sub.pricing_id:
                raise ValueError("New pricing is the same as the current one.")

            old_pricing = old_sub.pricing
            now = timezone.now()

            # ── Proration ───────────────────────────────────────────────────
            proration_amount = compute_proration(old_sub, old_pricing, new_pricing, now)

            # Cancel old subscription without going through the full cancel flow
            # (avoids deprovisioning services — customer keeps access during switch)
            old_sub.status = Subscription.Status.CANCELLED
            old_sub.save(update_fields=["status", "updated_at"])

            old_license = old_sub.license
            old_license.status = License.Status.REVOKED
            old_license.revoked_at = now
            old_license.save(update_fields=["status", "revoked_at"])

            OutboxEvent.objects.create(
                event_type="subscription.plan_changed",
                payload={
                    "old_subscription_id": str(old_sub.id),
                    "customer_id": str(old_sub.customer_id),
                    "old_pricing_id": str(old_pricing.id),
                    "new_pricing_id": str(new_pricing_id),
                    "proration_amount": str(proration_amount),
                },
            )

            # Create new subscription with the new pricing
            new_expiry = compute_expiry(now, new_pricing)

            new_sub = Subscription.objects.create(
                customer_id=old_sub.customer_id,
                product=old_sub.product,
                pricing=new_pricing,
                status=Subscription.Status.ACTIVE,
                starts_at=now,
                expires_at=new_expiry,
            )

            new_license = License.objects.create(
                subscription=new_sub,
                customer_id=old_sub.customer_id,
                key=License.generate_key(),
                status=License.Status.ACTIVE,
                valid_from=now,
                valid_until=new_expiry,
            )

            # Carry over existing service accesses — no re-provisioning needed
            for sa in old_license.service_accesses.all():
                ServiceAccess.objects.create(
                    license=new_license,
                    service_key=sa.service_key,
                    status=sa.status,
                    external_id=sa.external_id,
                    config=sa.config,
                    provisioned_at=sa.provisioned_at,
                )

            # Create proration invoice when upgrading (new > old) and amount is meaningful.
            if proration_amount > decimal.Decimal("0.01"):
                import datetime

                from apps.billing.models import Invoice

                proration_invoice = Invoice.objects.create(
                    customer_id=old_sub.customer_id,
                    subscription=new_sub,
                    invoice_type=Invoice.Type.SUBSCRIPTION,
                    description=(
                        f"Ajuste proporcional — mudança de plano "
                        f"({old_pricing.billing_cycle} → {new_pricing.billing_cycle})"
                    ),
                    amount=proration_amount,
                    due_date=timezone.localdate() + datetime.timedelta(days=3),
                )
                OutboxEvent.objects.create(
                    event_type="renewal_invoice.created",
                    payload={
                        "invoice_id": str(proration_invoice.id),
                        "customer_id": str(old_sub.customer_id),
                        "subscription_id": str(new_sub.id),
                    },
                )

            OutboxEvent.objects.create(
                event_type="subscription.created",
                payload={
                    "subscription_id": str(new_sub.id),
                    "license_id": str(new_license.id),
                    "customer_id": str(new_sub.customer_id),
                    "product_slug": new_sub.product.slug,
                    "service_keys": list(
                        new_license.service_accesses.values_list("service_key", flat=True)
                    ),
                },
            )

        return new_sub


def compute_expiry(starts_at, pricing) -> datetime:
    from apps.products.models import Pricing

    cycle = pricing.billing_cycle
    if cycle == Pricing.BillingCycle.MONTHLY:
        return starts_at + timedelta(days=30)
    if cycle == Pricing.BillingCycle.ANNUAL:
        return starts_at + timedelta(days=365)
    # LIFETIME and ONE_TIME are both perpetual — 100 years effectively
    return starts_at + timedelta(days=36500)


def compute_proration(old_sub, old_pricing, new_pricing, now) -> decimal.Decimal:
    """
    Returns the amount the customer owes for upgrading mid-cycle.

    Formula: (new_price - old_price) x remaining_days / cycle_days

    Returns Decimal("0") when:
    - downgrading (new_price <= old_price)
    - non-recurring plans (one_time / lifetime)
    - less than 1 day remaining on the old plan
    """
    from apps.products.models import Pricing

    cycle = old_pricing.billing_cycle
    if cycle not in (Pricing.BillingCycle.MONTHLY, Pricing.BillingCycle.ANNUAL):
        return decimal.Decimal("0")

    price_diff = new_pricing.amount - old_pricing.amount
    if price_diff <= 0:
        return decimal.Decimal("0")

    remaining_seconds = (old_sub.expires_at - now).total_seconds()
    if remaining_seconds <= 0:
        return decimal.Decimal("0")

    cycle_days = 30 if cycle == Pricing.BillingCycle.MONTHLY else 365
    remaining_days = decimal.Decimal(str(remaining_seconds / 86400))
    proration = (price_diff * remaining_days / decimal.Decimal(cycle_days)).quantize(
        decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
    )
    return max(proration, decimal.Decimal("0"))
