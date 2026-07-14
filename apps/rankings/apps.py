from django.apps import AppConfig


class RankingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rankings"

    def ready(self):
        import apps.rankings.signals  # noqa: F401

        # Start background Discord scheduler after apps are loaded.
        try:
            from apps.rankings.services.scheduler import start_discord_scheduler

            start_discord_scheduler()
        except Exception:
            # Never prevent app startup due to scheduler issues.
            import logging

            logging.getLogger(__name__).exception(
                "Failed to start Discord notification scheduler."
            )
