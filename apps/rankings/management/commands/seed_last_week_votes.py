import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.characters.models import Character
from apps.rankings.models import CharacterRanking, Duelist


def ranking_last_week_for_rank(rank, total):
    if rank == 1:
        return random.randint(22, 48)
    if rank == 2:
        return random.randint(14, 30)
    if rank == 3:
        return random.randint(9, 20)
    if rank <= max(4, total // 2):
        return random.randint(5, 14)
    if rank <= max(5, (total * 3) // 4):
        return random.randint(2, 8)
    return random.randint(1, 5)


def duelist_last_week_for_rank(rank, total):
    if rank == 1:
        return random.randint(18, 36)
    if rank == 2:
        return random.randint(12, 22)
    if rank == 3:
        return random.randint(8, 15)
    if rank <= max(4, total // 2):
        return random.randint(4, 11)
    if rank <= max(5, (total * 3) // 4):
        return random.randint(2, 6)
    return random.randint(1, 3)


class Command(BaseCommand):
    help = (
        "Seed last_week_votes for character rankings and duelists "
        "without changing current weekly or all-time totals."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducible distribution.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])
        ranking_updates = []
        duelist_updates = []

        for character in Character.objects.all().order_by("slug"):
            rankings = list(
                CharacterRanking.objects.filter(character=character).order_by("pk")
            )
            total = len(rankings)
            if not total:
                continue

            shuffled = rankings[:]
            random.shuffle(shuffled)
            vote_counts = sorted(
                [
                    ranking_last_week_for_rank(rank, total)
                    for rank in range(1, total + 1)
                ],
                reverse=True,
            )
            for ranking, vote_count in zip(shuffled, vote_counts):
                ranking.last_week_votes = vote_count
                ranking_updates.append(ranking)

        for region, _label in Duelist.REGION_CHOICES:
            duelists = list(Duelist.objects.filter(region=region).order_by("pk"))
            total = len(duelists)
            if not total:
                continue

            shuffled = duelists[:]
            random.shuffle(shuffled)
            vote_counts = sorted(
                [
                    duelist_last_week_for_rank(rank, total)
                    for rank in range(1, total + 1)
                ],
                reverse=True,
            )
            for duelist, vote_count in zip(shuffled, vote_counts):
                duelist.last_week_votes = vote_count
                duelist_updates.append(duelist)

        CharacterRanking.objects.bulk_update(ranking_updates, ["last_week_votes"])
        Duelist.objects.bulk_update(duelist_updates, ["last_week_votes"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded last_week_votes for {len(ranking_updates)} rankings "
                f"and {len(duelist_updates)} duelists."
            )
        )
