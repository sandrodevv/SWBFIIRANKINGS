from django.core.management.base import BaseCommand

from apps.rankings.services.player_votes import sync_all_player_all_time_votes


class Command(BaseCommand):
    help = "Recompute Player.all_time_votes from character ranking totals."

    def handle(self, *args, **options):
        updated = sync_all_player_all_time_votes()
        self.stdout.write(
            self.style.SUCCESS(f"Synced all-time vote totals for {updated} player(s).")
        )
