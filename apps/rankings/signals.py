from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.rankings.models import CharacterRanking
from apps.rankings.services.pfp import recalculate_all_pfp_scores
from apps.rankings.services.player_votes import sync_player_all_time_votes


@receiver(post_save, sender=CharacterRanking)
def refresh_pfp_on_ranking_save(sender, instance, **kwargs):
    sync_player_all_time_votes(instance.player)
    recalculate_all_pfp_scores()


@receiver(post_delete, sender=CharacterRanking)
def refresh_pfp_on_ranking_delete(sender, instance, **kwargs):
    sync_player_all_time_votes(instance.player)
    recalculate_all_pfp_scores()
