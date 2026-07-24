from django.core.exceptions import ValidationError
from django.db import transaction

from apps.characters.models import Character
from apps.rankings.models import CharacterRanking, Duelist, Player
from apps.rankings.services.discord import notify_player_registration


def _reset_ranking_votes(ranking):
    ranking.votes = 0
    ranking.last_week_votes = 0
    ranking.all_time_votes = 0
    ranking.vote_records.all().delete()


def _reset_duelist_votes(duelist):
    duelist.votes = 0
    duelist.last_week_votes = 0
    duelist.all_time_votes = 0
    duelist.vote_records.all().delete()


@transaction.atomic
def set_player_side_assignment(player, character):
    side = character.side
    ranking = player.rankings.filter(character__side=side).select_related("character").first()

    if ranking:
        if ranking.character_id == character.id:
            return ranking, False
        ranking.character = character
        _reset_ranking_votes(ranking)
        ranking.full_clean()
        ranking.save()
        return ranking, True

    ranking = CharacterRanking(player=player, character=character)
    ranking.full_clean()
    ranking.save()
    return ranking, True


def assign_player_characters(player, hero_character, villain_character):
    if hero_character.side != Character.SIDE_HERO:
        raise ValidationError({"hero_character": "Selected character must be a Hero."})
    if villain_character.side != Character.SIDE_VILLAIN:
        raise ValidationError({"villain_character": "Selected character must be a Villain."})

    _, hero_changed = set_player_side_assignment(player, hero_character)
    _, villain_changed = set_player_side_assignment(player, villain_character)
    return hero_changed, villain_changed


def assign_player_duelist(player, region, character):
    if region not in {choice[0] for choice in Duelist.REGION_CHOICES}:
        raise ValidationError({"duelist_region": "Select a valid region (EU, US, or AU)."})
    if character is None:
        raise ValidationError({"duelist_character": "Select a character for the duelist ranking."})
    if character.combat_type != Character.COMBAT_SABER:
        raise ValidationError(
            {"duelist_character": "Duelists can only represent Saber heroes (no blasters or balls)."}
        )

    if hasattr(player, "duelist"):
        duelist = player.duelist
        character_changed = duelist.character_id != character.id
        region_changed = duelist.region != region
        if not character_changed and not region_changed:
            return duelist, False, False

        duelist.region = region
        duelist.character = character
        if character_changed:
            _reset_duelist_votes(duelist)
        duelist.full_clean()
        duelist.save()
        return duelist, True, character_changed

    duelist = Duelist(player=player, region=region, character=character)
    duelist.full_clean()
    duelist.save()
    return duelist, True, False


@transaction.atomic
def create_player_with_assignments(
    nickname,
    username,
    *,
    discord_url="",
    steam_url="",
    twitch_url="",
    youtube_url="",
    register_character_rankings=True,
    hero_character=None,
    villain_character=None,
    register_duelist=False,
    duelist_region=None,
    duelist_character=None,
):
    if not register_character_rankings and not register_duelist:
        raise ValidationError(
            "Select at least one option: Hero & Villain rankings, Best Duelist, or both."
        )

    player = Player(
        nickname=nickname,
        username=username,
        discord_url=discord_url or "",
        steam_url=steam_url or "",
        twitch_url=twitch_url or "",
        youtube_url=youtube_url or "",
    )
    player.full_clean()
    player.save()

    if register_character_rankings:
        assign_player_characters(player, hero_character, villain_character)

    if register_duelist:
        assign_player_duelist(player, duelist_region, duelist_character)

    player_id = player.pk
    transaction.on_commit(lambda: _notify_registration(player_id))
    return player


def _notify_registration(player_id):
    player = Player.objects.filter(pk=player_id).first()
    if player:
        notify_player_registration(player)


@transaction.atomic
def complete_player_assignments(
    player,
    *,
    assign_character_rankings=False,
    hero_character=None,
    villain_character=None,
    assign_duelist=False,
    duelist_region=None,
    duelist_character=None,
):
    if not assign_character_rankings and not assign_duelist:
        raise ValidationError(
            "Select at least one missing assignment to add for this player."
        )

    has_hero = player.rankings.filter(character__side=Character.SIDE_HERO).exists()
    has_villain = player.rankings.filter(character__side=Character.SIDE_VILLAIN).exists()
    has_rankings = has_hero and has_villain
    has_duelist = hasattr(player, "duelist")

    if assign_character_rankings:
        if has_rankings:
            raise ValidationError(
                {"assign_character_rankings": f"{player.nickname} already has Hero & Villain rankings."}
            )
        assign_player_characters(player, hero_character, villain_character)

    if assign_duelist:
        if has_duelist:
            raise ValidationError(
                {"assign_duelist": f"{player.nickname} is already registered as a Best Duelist."}
            )
        assign_player_duelist(player, duelist_region, duelist_character)

    player_id = player.pk
    transaction.on_commit(lambda: _notify_registration(player_id))
    return player


@transaction.atomic
def modify_player_assignments(
    player,
    *,
    modify_character_rankings=False,
    hero_character=None,
    villain_character=None,
    modify_duelist=False,
    duelist_region=None,
    duelist_character=None,
):
    if not modify_character_rankings and not modify_duelist:
        raise ValidationError("Select at least one assignment to modify.")

    has_hero = player.rankings.filter(character__side=Character.SIDE_HERO).exists()
    has_villain = player.rankings.filter(character__side=Character.SIDE_VILLAIN).exists()
    has_rankings = has_hero and has_villain
    has_duelist = hasattr(player, "duelist")

    result = {
        "hero_changed": False,
        "villain_changed": False,
        "duelist_changed": False,
        "duelist_votes_reset": False,
    }

    if modify_character_rankings:
        if not has_rankings:
            raise ValidationError(
                {
                    "modify_character_rankings": (
                        f"{player.nickname} does not have Hero & Villain rankings to modify."
                    )
                }
            )
        hero_changed, villain_changed = assign_player_characters(
            player, hero_character, villain_character
        )
        result["hero_changed"] = hero_changed
        result["villain_changed"] = villain_changed

    if modify_duelist:
        if not has_duelist:
            raise ValidationError(
                {"modify_duelist": f"{player.nickname} is not registered as a Best Duelist."}
            )
        _, duelist_changed, votes_reset = assign_player_duelist(
            player, duelist_region, duelist_character
        )
        result["duelist_changed"] = duelist_changed
        result["duelist_votes_reset"] = votes_reset

    if not any(
        [
            result["hero_changed"],
            result["villain_changed"],
            result["duelist_changed"],
        ]
    ):
        raise ValidationError("No changes detected. Pick different characters or region.")

    return player, result


def set_player_name_effects(player, name_burning, name_smoke, name_glitch):
    burning = bool(name_burning)
    smoke = bool(name_smoke)
    glitch = bool(name_glitch)
    changed = (
        player.name_burning != burning
        or player.name_smoke != smoke
        or player.name_glitch != glitch
    )
    if not changed:
        return player, False
    player.name_burning = burning
    player.name_smoke = smoke
    player.name_glitch = glitch
    player.save(update_fields=["name_burning", "name_smoke", "name_glitch"])
    return player, True


def set_player_links(player, discord_url="", steam_url="", twitch_url="", youtube_url=""):
    discord = (discord_url or "").strip()
    steam = (steam_url or "").strip()
    twitch = (twitch_url or "").strip()
    youtube = (youtube_url or "").strip()
    changed = (
        player.discord_url != discord
        or player.steam_url != steam
        or player.twitch_url != twitch
        or player.youtube_url != youtube
    )
    if not changed:
        return player, False
    player.discord_url = discord
    player.steam_url = steam
    player.twitch_url = twitch
    player.youtube_url = youtube
    player.save(update_fields=["discord_url", "steam_url", "twitch_url", "youtube_url"])
    return player, True
