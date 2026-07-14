import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.characters.models import Character
from apps.rankings.models import Duelist, Player

REGIONS = [Duelist.REGION_EU, Duelist.REGION_US, Duelist.REGION_AU]

DUELIST_NICKNAMES = [
    "SaberStorm",
    "BladeRunnerBF",
    "KyberKnight",
    "DuelAce",
    "FormFourFox",
    "MakashiMain",
    "SoresuShield",
    "AtaruAce",
    "JuyoJuggernaut",
    "NimanNova",
    "CrossguardX",
    "TwinBlade",
    "RedSaberRex",
    "BlueBlade",
    "GreenGuard",
    "PurplePulse",
    "TempleGuard",
    "SithSparrer",
    "JediDuelist",
    "ForceFencer",
    "ParryPro",
    "RiposteRank",
    "LungeLegend",
    "ClashChamp",
    "GuardBreak",
    "PerfectParry",
    "SaberShowdown",
    "DuelDesk",
    "ArenaAce",
    "1v1King",
    "HvVHero",
    "LightsaberLab",
    "MaulMirror",
    "VaderVault",
    "KenobiKeep",
]


class Command(BaseCommand):
    help = "Seed Best Duelist profiles (saber characters only) for existing or new players."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=30,
            help="How many duelist profiles to create (default: 30).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = max(0, options["count"])
        if count == 0:
            self.stdout.write("Nothing to seed.")
            return

        sabers = list(Character.saber_queryset())
        if not sabers:
            self.stderr.write("No saber characters found. Seed characters first.")
            return

        random.seed(42)
        created = 0

        candidates = list(Player.objects.filter(duelist__isnull=True).order_by("id"))
        random.shuffle(candidates)

        for player in candidates:
            if created >= count:
                break
            self._create_duelist(player, sabers)
            created += 1

        nickname_index = 0
        while created < count:
            while nickname_index < len(DUELIST_NICKNAMES):
                nickname = DUELIST_NICKNAMES[nickname_index]
                nickname_index += 1
                if not Player.objects.filter(nickname__iexact=nickname).exists():
                    break
            else:
                nickname = f"DuelistSeed{created + 1}"
                if Player.objects.filter(nickname__iexact=nickname).exists():
                    nickname = f"DuelistSeed{created + 1}-{random.randint(100, 999)}"

            player = Player(nickname=nickname, username=None)
            player.full_clean()
            player.save()
            self._create_duelist(player, sabers)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created} duelists. Total now: {Duelist.objects.count()}."
            )
        )

    def _create_duelist(self, player, sabers):
        character = random.choice(sabers)
        region = random.choice(REGIONS)
        weekly = random.randint(0, 120)
        # Populate last_week_votes so Discord weekly-winner webhooks have data
        # before a real weekly reset has run.
        last_week = random.randint(max(weekly, 1), max(weekly, 1) + 80)
        all_time = last_week + weekly + random.randint(20, 300)
        duelist = Duelist(
            player=player,
            region=region,
            character=character,
            votes=weekly,
            last_week_votes=last_week,
            all_time_votes=all_time,
        )
        duelist.full_clean()
        duelist.save()
