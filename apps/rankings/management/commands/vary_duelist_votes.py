import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.rankings.models import Duelist


def votes_for_rank(rank, total):
    if rank == 1:
        return random.randint(180, 320)
    if rank == 2:
        return random.randint(130, 179)
    if rank == 3:
        return random.randint(90, 129)
    if rank <= max(4, total // 2):
        return random.randint(45, 89)
    if rank <= max(5, (total * 3) // 4):
        return random.randint(15, 44)
    return random.randint(2, 14)


class Command(BaseCommand):
    help = "Assign varied weekly and all-time votes to duelists by region."

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducible vote distribution.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])
        to_update = []

        for region, _label in Duelist.REGION_CHOICES:
            duelists = list(Duelist.objects.filter(region=region).order_by("pk"))
            total = len(duelists)
            if not total:
                continue

            shuffled = duelists[:]
            random.shuffle(shuffled)
            vote_counts = sorted(
                [votes_for_rank(rank, total) for rank in range(1, total + 1)],
                reverse=True,
            )

            for duelist, vote_count in zip(shuffled, vote_counts):
                duelist.votes = vote_count
                duelist.all_time_votes = vote_count
                to_update.append(duelist)

        Duelist.objects.bulk_update(to_update, ["votes", "all_time_votes"])

        self.stdout.write(
            self.style.SUCCESS(f"Updated votes for {len(to_update)} duelists.")
        )
