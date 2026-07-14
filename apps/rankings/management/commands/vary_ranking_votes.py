import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from apps.characters.models import Character
from apps.rankings.models import CharacterRanking, Player
from apps.rankings.services.pfp import recalculate_all_pfp_scores


def votes_for_rank(rank, total_players):
    if rank == 1:
        return random.randint(520, 960)
    if rank == 2:
        return random.randint(380, 520)
    if rank == 3:
        return random.randint(260, 379)
    if rank <= max(4, total_players // 2):
        return random.randint(140, 259)
    if rank <= max(5, (total_players * 3) // 4):
        return random.randint(45, 139)
    return random.randint(12, 44)


class Command(BaseCommand):
    help = "Assign varied vote totals to all character rankings for visible PFP spread."

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
        updated = 0
        to_update = []

        for character in Character.objects.all().order_by("slug"):
            rankings = list(
                CharacterRanking.objects.filter(character=character)
                .select_related("player")
                .order_by("pk")
            )
            total = len(rankings)
            if not total:
                continue

            shuffled = rankings[:]
            random.shuffle(shuffled)
            vote_counts = sorted(
                [votes_for_rank(rank, total) for rank in range(1, total + 1)],
                reverse=True,
            )

            for ranking, vote_count in zip(shuffled, vote_counts):
                ranking.votes = vote_count
                ranking.all_time_votes = vote_count
                to_update.append(ranking)
                updated += 1

        CharacterRanking.objects.bulk_update(to_update, ["votes", "all_time_votes"])

        for player in Player.objects.all():
            total = (
                player.rankings.aggregate(total=Sum("all_time_votes"))["total"] or 0
            )
            player.all_time_votes = total
            player.save(update_fields=["all_time_votes"])

        pfp_count = recalculate_all_pfp_scores()

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated votes for {updated} rankings and recalculated {pfp_count} PFP scores."
            )
        )
