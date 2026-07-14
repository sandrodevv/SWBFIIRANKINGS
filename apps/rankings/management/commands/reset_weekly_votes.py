from django.core.management.base import BaseCommand

from apps.rankings.services.weekly_reset import reset_weekly_votes


class Command(BaseCommand):
    help = "Reset weekly vote counts to zero for all character rankings."

    def handle(self, *args, **options):
        period = reset_weekly_votes()
        self.stdout.write(
            self.style.SUCCESS(
                f"Weekly votes reset. New period started at {period.started_at.isoformat()}."
            )
        )
