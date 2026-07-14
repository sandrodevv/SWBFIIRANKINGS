from django.core.management.base import BaseCommand

from apps.rankings.services.pfp import recalculate_all_pfp_scores


class Command(BaseCommand):
    help = "Recalculate Pound-for-Pound scores for all character rankings."

    def handle(self, *args, **options):
        count = recalculate_all_pfp_scores()
        self.stdout.write(self.style.SUCCESS(f"Recalculated PFP scores for {count} rankings."))
