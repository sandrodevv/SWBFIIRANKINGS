from django.core.management.base import BaseCommand

from apps.rankings.services.pfp_discord import send_pfp_ending_soon_notification


class Command(BaseCommand):
    help = (
        "Send the current PFP rankings Discord webhook if the weekly period "
        "is within the configured lead window (or force with --force)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Send even outside the lead window / allow resend for the "
                "current period (still uses the same ranking data source)."
            ),
        )

    def handle(self, *args, **options):
        result = send_pfp_ending_soon_notification(force=options["force"])
        styles = {
            "sent": self.style.SUCCESS,
            "failed": self.style.ERROR,
            "error": self.style.ERROR,
            "skipped_duplicate": self.style.WARNING,
            "skipped_outside_window": self.style.NOTICE,
        }
        style = styles.get(result, self.style.NOTICE)
        self.stdout.write(style(f"PFP Discord notification result: {result}"))
