from django.core.management.base import BaseCommand

from apps.rankings.models import Duelist
from apps.rankings.services.duelist_discord import (
    send_duelist_weekly_winners_notification,
)


class Command(BaseCommand):
    help = (
        "Send the previous-week top AU duelist winners Discord webhook "
        "(uses last_week_votes). Use --force to allow a resend for this period."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow resending for the current period if already sent.",
        )

    def handle(self, *args, **options):
        result = send_duelist_weekly_winners_notification(
            Duelist.REGION_AU,
            force=options["force"],
        )
        styles = {
            "sent": self.style.SUCCESS,
            "failed": self.style.ERROR,
            "error": self.style.ERROR,
            "skipped_duplicate": self.style.WARNING,
        }
        style = styles.get(result, self.style.NOTICE)
        self.stdout.write(
            style(f"AU duelist Discord notification result: {result}")
        )
