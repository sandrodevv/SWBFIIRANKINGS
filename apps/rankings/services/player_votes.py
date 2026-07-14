from django.db.models import Sum

from apps.rankings.models import Player


def sync_player_all_time_votes(player):
    if player is None or not player.pk:
        return 0

    total = player.rankings.aggregate(total=Sum("all_time_votes"))["total"] or 0
    if player.all_time_votes != total:
        player.all_time_votes = total
        player.save(update_fields=["all_time_votes"])
    return total


def sync_all_player_all_time_votes():
    updated = 0
    for player in Player.objects.all():
        before = player.all_time_votes
        after = sync_player_all_time_votes(player)
        if before != after:
            updated += 1
    return updated
