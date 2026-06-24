from rest_framework.permissions import BasePermission


class IsActiveCustomer(BasePermission):
    """
    Rejects requests from customers whose status is not ACTIVE.

    Usage: add to DEFAULT_PERMISSION_CLASSES or per-view throttle_classes.
    Staff users bypass this check so admins can still access the API.
    """

    message = "Sua conta está suspensa ou cancelada."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return True  # let IsAuthenticated handle this

        if request.user.is_staff:
            return True

        # Lazy imports to avoid circular dependency at module load time
        # (shared.exceptions imports rest_framework which reads DEFAULT_PERMISSION_CLASSES
        # which would import this module again before it finishes initialising)
        from apps.customers.models import Customer, CustomerProfile
        from shared.exceptions import SubscriptionSuspendedError

        profile = (
            CustomerProfile.objects.select_related("customer").filter(user=request.user).first()
        )
        if profile is None:
            return True  # no profile = admin user or not yet linked

        customer = profile.customer
        if customer.status == Customer.Status.ACTIVE:
            return True

        if customer.status == Customer.Status.SUSPENDED:
            raise SubscriptionSuspendedError()

        self.message = "Sua conta foi cancelada."
        return False
