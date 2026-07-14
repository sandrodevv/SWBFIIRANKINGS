import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.characters.models import Character
from apps.rankings.models import CharacterRanking, Player

HEROES = [
    ("Luke Skywalker", "luke-skywalker"),
    ("Leia Organa", "leia-organa"),
    ("Han Solo", "han-solo"),
    ("Chewbacca", "chewbacca"),
    ("Lando Calrissian", "lando-calrissian"),
    ("Rey", "rey"),
    ("Finn", "finn"),
    ("Obi-Wan Kenobi", "obi-wan-kenobi"),
    ("Anakin Skywalker", "anakin-skywalker"),
    ("Yoda", "yoda"),
    ("BB-8", "bb-8"),
]

VILLAINS = [
    ("Darth Vader", "darth-vader"),
    ("Emperor Palpatine", "emperor-palpatine"),
    ("Darth Maul", "darth-maul"),
    ("Boba Fett", "boba-fett"),
    ("Bossk", "bossk"),
    ("Iden Versio", "iden-versio"),
    ("Kylo Ren", "kylo-ren"),
    ("Captain Phasma", "captain-phasma"),
    ("General Grievous", "general-grievous"),
    ("Count Dooku", "count-dooku"),
    ("BB-9E", "bb-9e"),
]

SABER_SLUGS = {
    "anakin-skywalker",
    "luke-skywalker",
    "obi-wan-kenobi",
    "rey",
    "yoda",
    "count-dooku",
    "darth-maul",
    "darth-vader",
    "kylo-ren",
    "general-grievous",
}

BALL_SLUGS = {
    "bb-8",
    "bb-9e",
}


def combat_type_for_slug(slug):
    if slug in SABER_SLUGS:
        return Character.COMBAT_SABER
    if slug in BALL_SLUGS:
        return Character.COMBAT_BALL
    return Character.COMBAT_BLASTER

NICKNAME_POOL = [
    "GalaxyKing", "SithMaster", "LukeMain", "ForceCrusher", "JediMaster",
    "DarkKnight", "VaderMain", "SkywalkerPro", "BlasterAce", "RebelLeader",
    "ImperialElite", "CloneCommander", "DroidHunter", "Sabermaster", "ForceGhost",
    "HothHero", "EndorVet", "DeathStarDuo", "TatooineTitan", "NabooKnight",
    "CoruscantKing", "KaminoAce", "MustafarMain", "BespinBoss", "JakkuJumper",
    "Starkiller", "NightSister", "MandalorianX", "WookieeWarrior", "SenateGuard",
    "PilotOne", "AceSquadron", "IonCannon", "ThermalDet", "HeroOfHoth",
    "VillainArc", "PalpatineFan", "MaulMode", "GrievousGrip", "PhasmaPrime",
    "RenRampage", "DookuDuelist", "FettFanatic", "BosskBrawler", "IdenImpact",
    "YodaYoda", "AnakinAce", "ObiOne", "LeiaLegend", "HanShotFirst",
    "ChewieChamp", "LandoLuck", "ReyRising", "FinnForce", "BB8Buddy",
    "GalacticAce", "StarfighterX", "HyperdriveHero", "LightsideLord", "DarksideDuke",
    "RepublicRogue", "EmpireElite", "ResistanceRex", "FirstOrderFox", "CloneWarsKid",
    "BattlefrontPro", "GalacticLegend", "HeroHunter", "VillainVortex", "RankedRunner",
    "VoteMagnet", "TopTenTitan", "PodiumPlayer", "ChampionChaser", "LeaderboardLegend",
    "ForceAwakened", "SkywalkerLine", "OrganaOutlaw", "SoloSpecial", "CalrissianCool",
    "KenobiKnight", "SkywalkerAnakin", "PalpatinePower", "MaulMenace", "VaderVoid",
    "GrievousGeneral", "PhasmaPhoenix", "VersioVanguard", "RenReborn", "DookuDark",
    "FettFury", "BosskBeast", "BB9EBot", "GalaxyGladiator", "FrontlineFighter",
    "OrbitalOverlord", "SectorStriker", "NebulaNomad", "AsteroidAce", "FleetCommander",
    "Sandro", "VexMain", "NovaStrike", "CrimsonAce", "ShadowJedi",
    "IronSith", "PulsePilot", "EchoKnight", "RiftWalker", "OnyxBlade",
]

USERNAME_POOL = [
    "galaxyruler", "bestani", "lukemain_bf", "forcecrush", "jedimaster_01",
    "darkknight_x", "vadermain", "skywalkerpro", "blasterace", "rebelleader",
    "imperial_elite", "clonecmdr", "droidhunter", "sabermaster", "forceghost",
    "hothhero", "endorvet", "deathstarduo", "tatooinetitan", "nabooknight",
    "coruscantking", "kaminoace", "mustafarmain", "bespinboss", "jakku_jumper",
    "starkiller99", "nightsister", "mando_x", "wookieewarrior", "senateguard",
    "pilotone", "acesquadron", "ioncannon", "thermaldet", "herohoth",
    "villainarc", "palpatinefan", "maulmode", "grievousgrip", "phasma_prime",
    "renrampage", "dookuduelist", "fettfanatic", "bosskbrawler", "idenimpact",
    "yodayoda", "anakinace", "obione", "leialegend", "hanshotfirst",
    "chewiechamp", "landoluck", "reyrising", "finnforce", "bb8buddy",
    "galacticace", "starfighterx", "hyperdrivehero", "lightsidelord", "darksideduke",
    "republicrogue", "empireelite", "resistancerex", "firstorderfox", "clonewarskid",
    "battlefrontpro", "galacticlegend", "herohunter", "villainvortex", "rankedrunner",
    "votemagnet", "topten_titan", "podiumplayer", "championchaser", "leaderboardlegend",
    "forceawakened", "skywalkerline", "organaoutlaw", "solospecial", "calrissiancool",
    "kenobiknight", "skywalkeranakin", "palpatinepower", "maulmenace", "vadervoid",
    "grievousgeneral", "phasmaphoenix", "versiovanguard", "renreborn", "dookudark",
    "fettfury", "bosskbeast", "bb9ebot", "galaxygladiator", "frontlinefighter",
    "orbitaloverlord", "sectorstriker", "nebulanomad", "asteroidace", "fleetcommander",
    "sandro", "vexmain", "novastrike", "crimsonace", "shadowjedi",
    "ironsith", "pulsepilot", "echoknight", "riftwalker", "onyxblade",
]

DESCRIPTIONS = {
    "luke-skywalker": (
        "The Jedi who became the galaxy's greatest hope, wielding the Force against the darkness."
    ),
    "leia-organa": (
        "A fearless rebel commander whose determination keeps the fight for freedom alive."
    ),
    "han-solo": (
        "A daring smuggler turned hero, relying on instinct, courage, and a lucky shot."
    ),
    "chewbacca": (
        "A mighty Wookiee warrior whose strength and loyalty make him a battlefield monster."
    ),
    "yoda": "An ancient Jedi Master whose small stature hides overwhelming power.",
    "obi-wan-kenobi": (
        "A legendary Jedi survivor who stands as a symbol of patience and hope."
    ),
    "anakin-skywalker": (
        "The Chosen One, a warrior of unmatched potential before his fall into darkness."
    ),
    "rey": (
        "A desert scavenger who discovered the Force and rose to challenge the First Order."
    ),
    "finn": "A former stormtrooper who broke free and fought for a greater cause.",
    "lando-calrissian": (
        "A charming gambler and brilliant strategist who became a rebel legend."
    ),
    "darth-vader": (
        "The Empire's unstoppable enforcer, a fallen Jedi consumed by the dark side."
    ),
    "emperor-palpatine": (
        "The Sith mastermind who manipulated the galaxy into submission."
    ),
    "darth-maul": (
        "A warrior forged by hatred, driven by vengeance and endless rage."
    ),
    "kylo-ren": (
        "A conflicted dark warrior desperate to prove himself through power and fear."
    ),
    "count-dooku": (
        "A fallen Jedi whose elegance masks a ruthless Sith ambition."
    ),
    "general-grievous": (
        "A cybernetic killing machine built to hunt Jedi and spread terror."
    ),
    "boba-fett": (
        "The galaxy's most feared bounty hunter, a silent predator who never misses."
    ),
    "bossk": "A savage Trandoshan hunter who treats every battle as a hunt.",
    "iden-versio": (
        "An elite Imperial commander caught between loyalty and the truth."
    ),
    "captain-phasma": (
        "A ruthless First Order commander whose armor hides cold ambition."
    ),
    "bb-8": (
        "A fearless astromech droid whose courage proves even the smallest heroes can change history."
    ),
    "bb-9e": "A First Order security droid built to intimidate and control.",
}

PLAYERS_PER_CHARACTER = 10


def assign_players_to_characters(characters, players, players_per_character):
    assignments = {character.id: [] for character in characters}
    shuffled = players[:]
    random.shuffle(shuffled)

    for player in shuffled:
        open_characters = [
            character
            for character in characters
            if len(assignments[character.id]) < players_per_character
        ]
        if not open_characters:
            break
        character = min(open_characters, key=lambda item: len(assignments[item.id]))
        assignments[character.id].append(player)

    return assignments


def upsert_characters():
    """Create or update all Heroes/Villains with combat type and descriptions."""
    created_count = 0
    for name, slug in HEROES:
        _, created = Character.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "side": Character.SIDE_HERO,
                "combat_type": combat_type_for_slug(slug),
                "description": DESCRIPTIONS.get(slug, f"Top players for {name}."),
            },
        )
        created_count += int(created)

    for name, slug in VILLAINS:
        _, created = Character.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "side": Character.SIDE_VILLAIN,
                "combat_type": combat_type_for_slug(slug),
                "description": DESCRIPTIONS.get(slug, f"Top players for {name}."),
            },
        )
        created_count += int(created)

    return created_count


def find_static_character_image(slug):
    from django.conf import settings

    directory = settings.BASE_DIR / "frontend" / "static" / "images" / "characters"
    for extension in Character.STATIC_IMAGE_EXTENSIONS:
        path = directory / f"{slug}{extension}"
        if path.is_file():
            return path
    return None


def attach_static_images(*, replace_existing=False):
    """
    Copy matching files from frontend/static/images/characters/ into Character.image.

    Static files remain the deploy-friendly source; this also fills the ImageField
    so Django admin and media URLs work.
    """
    from django.core.files import File

    attached = 0
    missing = []
    for character in Character.objects.order_by("slug"):
        path = find_static_character_image(character.slug)
        if path is None:
            missing.append(character.slug)
            continue
        if character.image and not replace_existing:
            continue
        with path.open("rb") as handle:
            character.image.save(path.name, File(handle), save=True)
        attached += 1
    return attached, missing


class Command(BaseCommand):
    help = (
        "Seed characters, players, and rankings with realistic vote data. "
        "Use --characters-only for production (characters + images, no fake players)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recreate rankings for all characters (keeps characters and players).",
        )
        parser.add_argument(
            "--characters-only",
            action="store_true",
            help=(
                "Only create/update characters (with descriptions and combat types) "
                "and attach images from frontend/static/images/characters/. "
                "Does not create players, rankings, or votes."
            ),
        )
        parser.add_argument(
            "--replace-images",
            action="store_true",
            help="When attaching images, overwrite existing Character.image values.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options["force"]
        characters_only = options["characters_only"]
        replace_images = options["replace_images"]
        random.seed(42)

        characters_created = upsert_characters()
        images_attached, missing_images = attach_static_images(
            replace_existing=replace_images
        )

        if characters_only:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Characters-only seed complete: {characters_created} new characters, "
                    f"{images_attached} images attached, "
                    f"{Character.objects.count()} characters total."
                )
            )
            if missing_images:
                self.stdout.write(
                    self.style.WARNING(
                        "No static image found for: " + ", ".join(missing_images)
                    )
                )
            return

        players = []
        for nickname, username in zip(NICKNAME_POOL, USERNAME_POOL):
            player, _ = Player.objects.update_or_create(
                nickname=nickname,
                defaults={"username": username},
            )
            players.append(player)

        if force:
            CharacterRanking.objects.all().delete()
            Player.objects.update(all_time_votes=0)
        elif CharacterRanking.objects.exists():
            self.stdout.write("Rankings already exist. Use --force to rebuild.")
            return

        heroes = list(Character.objects.filter(side=Character.SIDE_HERO).order_by("slug"))
        villains = list(Character.objects.filter(side=Character.SIDE_VILLAIN).order_by("slug"))

        hero_assignments = assign_players_to_characters(heroes, players, PLAYERS_PER_CHARACTER)
        villain_assignments = assign_players_to_characters(
            villains, players, PLAYERS_PER_CHARACTER
        )

        rankings_created = 0
        for character in heroes + villains:
            assignment_map = (
                hero_assignments if character.side == Character.SIDE_HERO else villain_assignments
            )
            assigned_players = assignment_map[character.id]
            votes = sorted(
                [random.randint(50, 700) for _ in range(len(assigned_players))],
                reverse=True,
            )
            for player, vote_count in zip(assigned_players, votes):
                CharacterRanking.objects.create(
                    character=character,
                    player=player,
                    votes=vote_count,
                    all_time_votes=vote_count,
                )
                player.all_time_votes += vote_count
                player.save(update_fields=["all_time_votes"])
                rankings_created += 1

        from apps.rankings.services.pfp import recalculate_all_pfp_scores

        recalculate_all_pfp_scores()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {characters_created} new characters, "
                f"{images_attached} images attached, "
                f"{rankings_created} rankings created."
            )
        )
        if missing_images:
            self.stdout.write(
                self.style.WARNING(
                    "No static image found for: " + ", ".join(missing_images)
                )
            )