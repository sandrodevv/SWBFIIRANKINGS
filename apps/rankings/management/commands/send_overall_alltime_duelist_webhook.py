from django.core.management.base import BaseCommand

from apps.rankings.services.duelist_discord import (
    send_overall_alltime_duelist_notification,
)


class Command(BaseCommand):
    help = (
        "Send the overall all-time duelist leaderboard Discord webhook "
        "(uses all_time_votes across every region)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Resend even if already sent for the current voting period.",
        )

    def handle(self, *args, **options):
        result = send_overall_alltime_duelist_notification(force=options["force"])
        styles = {
            "sent": self.style.SUCCESS,
            "failed": self.style.ERROR,
            "error": self.style.ERROR,
            "skipped_duplicate": self.style.WARNING,
        }
        style = styles.get(result, self.style.NOTICE)
        self.stdout.write(
            style(f"Overall all-time duelist Discord notification result: {result}")
        )
