from django.core.exceptions import ValidationError

from apps.characters.models import Character


def player_side_assignment_conflict(player, character, exclude_ranking_id=None):
    if not player.pk:
        return None
    queryset = player.rankings.filter(character__side=character.side)
    if exclude_ranking_id:
        queryset = queryset.exclude(pk=exclude_ranking_id)
    return queryset.select_related("character").first()


def validate_player_side_assignment(player, character, exclude_ranking_id=None):
    if not player.pk:
        return
    existing = player_side_assignment_conflict(player, character, exclude_ranking_id)
    if existing:
        side_label = "Hero" if character.side == Character.SIDE_HERO else "Villain"
        raise ValidationError(
            f"{player.nickname} is already assigned to {existing.character.name} "
            f"({side_label}). Each player can only be ranked on one Hero and one Villain."
        )
