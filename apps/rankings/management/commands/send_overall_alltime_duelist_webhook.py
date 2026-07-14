from django.core.management.base import BaseCommand

from apps.rankings.services.duelist_discord import (
    send_overall_alltime_duelist_notification,
)


class Command(BaseCommand):
    help = (
        "Send the overall all-time duelist leaderboard Discord webhook "
        "(uses all_time_votes across every region)."
    )

    def handle(self, *args, **options):
        result = send_overall_alltime_duelist_notification()
        styles = {
            "sent": self.style.SUCCESS,
            "failed": self.style.ERROR,
            "error": self.style.ERROR,
        }
        style = styles.get(result, self.style.NOTICE)
        self.stdout.write(
            style(f"Overall all-time duelist Discord notification result: {result}")
        )
