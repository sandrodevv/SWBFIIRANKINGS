import hashlib
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.characters.models import Character
from apps.rankings.models import (
    CharacterRanking,
    Duelist,
    DuelistVoteRecord,
    Player,
    VoteRecord,
)
from apps.rankings.services.pfp import recalculate_all_pfp_scores
from apps.rankings.services.weekly_reset import reset_weekly_votes


def weekly_votes_for_rank(rank, total_players):
    if rank == 1:
        return random.randint(22, 48)
    if rank == 2:
        return random.randint(14, 30)
    if rank == 3:
        return random.randint(9, 20)
    if rank <= max(4, total_players // 2):
        return random.randint(5, 14)
    if rank <= max(5, (total_players * 3) // 4):
        return random.randint(2, 8)
    return random.randint(1, 5)


def duelist_weekly_votes_for_rank(rank, total):
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


def fake_hash(prefix, *parts):
    payload = f"{prefix}:" + ":".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode()).hexdigest()


class Command(BaseCommand):
    help = (
        "Simulate a new weekly voting period: reset weekly counts, "
        "add fresh votes, and create recent vote activity."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed",
            type=int,
            default=7,
            help="Random seed for vote distribution.",
        )
        parser.add_argument(
            "--reseed",
            action="store_true",
            help="Rebuild all rankings from seed_rankings before simulating the new week.",
        )
        parser.add_argument(
            "--recent-records",
            type=int,
            default=48,
            help="How many VoteRecord rows to create for the recent-votes feed.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])

        if options["reseed"]:
            self.stdout.write("Rebuilding rankings from seed_rankings --force ...")
            call_command("seed_rankings", force=True)
        elif not CharacterRanking.objects.exists():
            self.stdout.write("No rankings found — running seed_rankings ...")
            call_command("seed_rankings")

        deleted_records = VoteRecord.objects.count()
        deleted_duelist_records = DuelistVoteRecord.objects.count()
        VoteRecord.objects.all().delete()
        DuelistVoteRecord.objects.all().delete()

        period = reset_weekly_votes()
        self.stdout.write(
            f"Weekly period reset at {period.started_at.isoformat()} "
            f"(cleared {deleted_records} ranking and "
            f"{deleted_duelist_records} duelist vote records)."
        )

        rankings_updated = 0
        weekly_votes_added = 0
        ranking_updates = []

        for character in Character.objects.all().order_by("slug"):
            rankings = list(
                CharacterRanking.objects.filter(character=character)
                .select_related("player", "character")
                .order_by("pk")
            )
            total = len(rankings)
            if not total:
                continue

            shuffled = rankings[:]
            random.shuffle(shuffled)
            weekly_counts = sorted(
                [weekly_votes_for_rank(rank, total) for rank in range(1, total + 1)],
                reverse=True,
            )

            for ranking, weekly_count in zip(shuffled, weekly_counts):
                ranking.votes = weekly_count
                ranking.all_time_votes += weekly_count
                ranking_updates.append(ranking)
                weekly_votes_added += weekly_count
                rankings_updated += 1

        CharacterRanking.objects.bulk_update(
            ranking_updates,
            ["votes", "all_time_votes"],
        )

        duelists_updated = 0
        duelist_weekly_added = 0
        duelist_updates = []

        for region, _label in Duelist.REGION_CHOICES:
            duelists = list(Duelist.objects.filter(region=region).order_by("pk"))
            total = len(duelists)
            if not total:
                continue

            shuffled = duelists[:]
            random.shuffle(shuffled)
            weekly_counts = sorted(
                [
                    duelist_weekly_votes_for_rank(rank, total)
                    for rank in range(1, total + 1)
                ],
                reverse=True,
            )

            for duelist, weekly_count in zip(shuffled, weekly_counts):
                duelist.votes = weekly_count
                duelist.all_time_votes += weekly_count
                duelist_updates.append(duelist)
                duelist_weekly_added += weekly_count
                duelists_updated += 1

        Duelist.objects.bulk_update(duelist_updates, ["votes", "all_time_votes"])

        for player in Player.objects.all():
            total = player.rankings.aggregate(total=Sum("all_time_votes"))["total"] or 0
            player.all_time_votes = total
            player.save(update_fields=["all_time_votes"])

        records_target = options["recent_records"]
        rankings = list(
            CharacterRanking.objects.select_related("player", "character").order_by("?")[
                :records_target
            ]
        )
        now = timezone.now()
        vote_records = []

        for index, ranking in enumerate(rankings):
            minutes_ago = random.randint(3, 60 * 24 * 4)
            vote_records.append(
                VoteRecord(
                    character=ranking.character,
                    ranking=ranking,
                    ip_hash=fake_hash("sim-ip", index, ranking.id),
                    voter_hash=fake_hash("sim-voter", index, ranking.player_id),
                    voted_at=now - timedelta(minutes=minutes_ago),
                )
            )

        VoteRecord.objects.bulk_create(vote_records)

        duelist_records = []
        sampled_duelists = list(Duelist.objects.select_related("player").order_by("?")[:24])
        for index, duelist in enumerate(sampled_duelists):
            minutes_ago = random.randint(3, 60 * 24 * 4)
            duelist_records.append(
                DuelistVoteRecord(
                    duelist=duelist,
                    ip_hash=fake_hash("sim-duelist-ip", index, duelist.id),
                    voter_hash=fake_hash("sim-duelist-voter", index, duelist.player_id),
                    voted_at=now - timedelta(minutes=minutes_ago),
                )
            )
        DuelistVoteRecord.objects.bulk_create(duelist_records)

        pfp_count = recalculate_all_pfp_scores()

        self.stdout.write(
            self.style.SUCCESS(
                f"New week simulated: {rankings_updated} rankings updated "
                f"({weekly_votes_added} weekly votes), "
                f"{duelists_updated} duelists updated "
                f"({duelist_weekly_added} weekly votes), "
                f"{len(vote_records)} ranking + {len(duelist_records)} duelist "
                f"vote records created, {pfp_count} PFP scores recalculated."
            )
        )
