from django.core.management.base import BaseCommand
from django.db import transaction

from apps.characters.management.commands.seed_rankings import NICKNAME_POOL, USERNAME_POOL
from apps.rankings.models import Player


class Command(BaseCommand):
    help = "Assign distinct platform usernames to all seeded players."

    @transaction.atomic
    def handle(self, *args, **options):
        updated = 0
        for nickname, username in zip(NICKNAME_POOL, USERNAME_POOL):
            player = Player.objects.filter(nickname=nickname).first()
            if not player:
                continue

            conflict = Player.objects.filter(username=username).exclude(pk=player.pk).exists()
            if conflict:
                temp = f"_tmp_{player.pk}_{username}"
                Player.objects.filter(username=username).exclude(pk=player.pk).update(
                    username=temp
                )

            player.username = username
            player.save(update_fields=["username"])
            updated += 1

        for player in Player.objects.filter(username__startswith="_tmp_"):
            base = player.nickname.lower().replace(" ", "_")
            username = base
            counter = 1
            while Player.objects.filter(username=username).exclude(pk=player.pk).exists():
                username = f"{base}{counter}"
                counter += 1
            player.username = username
            player.save(update_fields=["username"])

        self.stdout.write(self.style.SUCCESS(f"Updated usernames for {updated} players."))
