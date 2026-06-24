from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "apps.notifications"
    verbose_name = "Notifications"

    def ready(self) -> None:
        # Import handler modules so their @register decorators execute at startup.
        import apps.licensing.handlers
        import apps.notifications.handlers
        import apps.support.handlers  # noqa: F401
