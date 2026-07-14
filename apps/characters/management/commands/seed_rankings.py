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
    "luke-skywalker": "Legendary Jedi who brings hope to the battlefield.",
    "darth-vader": "The dark lord whose presence dominates every match.",
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


class Command(BaseCommand):
    help = "Seed characters, players, and rankings with realistic vote data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recreate rankings for all characters (keeps characters and players).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options["force"]
        random.seed(42)

        characters_created = 0
        for name, slug in HEROES:
            _, created = Character.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "side": Character.SIDE_HERO,
                    "description": DESCRIPTIONS.get(slug, f"Top players for {name}."),
                },
            )
            characters_created += int(created)

        for name, slug in VILLAINS:
            _, created = Character.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "side": Character.SIDE_VILLAIN,
                    "description": DESCRIPTIONS.get(slug, f"Top players for {name}."),
                },
            )
            characters_created += int(created)

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
                f"Seed complete: {characters_created} new characters, {rankings_created} rankings created."
            )
        )
