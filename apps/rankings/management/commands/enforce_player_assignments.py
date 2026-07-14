from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from apps.characters.models import Character
from apps.rankings.models import CharacterRanking, Player


class Command(BaseCommand):
    help = (
        "Ensure each player is assigned to at most one Hero and one Villain ranking. "
        "Keeps the ranking with the highest all-time votes per side."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be removed without deleting.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        removed = 0

        for player in Player.objects.all():
            for side in (Character.SIDE_HERO, Character.SIDE_VILLAIN):
                rankings = list(
                    player.rankings.filter(character__side=side).order_by(
                        "-all_time_votes", "created_at"
                    )
                )
                if len(rankings) <= 1:
                    continue

                for duplicate in rankings[1:]:
                    removed += 1
                    message = (
                        f"Remove {player.nickname} from {duplicate.character.name} "
                        f"({side}, kept on {rankings[0].character.name})"
                    )
                    if dry_run:
                        self.stdout.write(message)
                    else:
                        duplicate.delete()

        if not dry_run:
            for player in Player.objects.all():
                total = (
                    player.rankings.aggregate(total=Sum("all_time_votes"))["total"] or 0
                )
                player.all_time_votes = total
                player.save(update_fields=["all_time_votes"])

        action = "Would remove" if dry_run else "Removed"
        self.stdout.write(self.style.SUCCESS(f"{action} {removed} duplicate ranking(s)."))
