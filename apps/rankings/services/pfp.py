from dataclasses import dataclass

from django.db.models import Count, Max

from apps.characters.models import Character
from apps.rankings.models import CharacterRanking

PFP_WEIGHT_PERCENTILE = 0.40
PFP_WEIGHT_VOTE = 0.35
PFP_WEIGHT_COMPETITION = 0.15
PFP_WEIGHT_CHAMPION = 0.10

PODIUM_BONUS_BY_RANK = {
    1: 100.0,
    2: 80.0,
    3: 60.0,
    4: 45.0,
    5: 30.0,
    6: 20.0,
    7: 12.0,
    8: 6.0,
}


def _podium_bonus(rank):
    return PODIUM_BONUS_BY_RANK.get(rank, 0.0)


@dataclass
class PfpMetrics:
    ranking_id: int
    rank: int
    votes: int
    percentile_score: float
    vote_score: float
    competition_score: float
    champion_bonus: float
    pfp_score: float


def _clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def calculate_pfp_metrics(rank, total_players, votes, max_votes, largest_character_size):
    if total_players <= 0 or rank <= 0:
        return None

    percentile_score = ((total_players - rank + 1) / total_players) * 100
    vote_score = _clamp((votes / max_votes) * 100) if max_votes > 0 else 0.0
    competition_score = (
        _clamp((total_players / largest_character_size) * 100)
        if largest_character_size > 0
        else 0.0
    )
    champion_bonus = _podium_bonus(rank)

    pfp_score = (
        percentile_score * PFP_WEIGHT_PERCENTILE
        + vote_score * PFP_WEIGHT_VOTE
        + competition_score * PFP_WEIGHT_COMPETITION
        + champion_bonus * PFP_WEIGHT_CHAMPION
    )

    return PfpMetrics(
        ranking_id=0,
        rank=rank,
        votes=votes,
        percentile_score=percentile_score,
        vote_score=vote_score,
        competition_score=competition_score,
        champion_bonus=champion_bonus,
        pfp_score=pfp_score,
    )


def _pfp_sort_key(metrics: PfpMetrics):
    return (
        -metrics.pfp_score,
        -metrics.percentile_score,
        -metrics.vote_score,
        metrics.rank,
        -metrics.votes,
    )


def get_pfp_leaderboard_queryset():
    """
    Canonical PFP leaderboard queryset used by the website API and Discord.

    Rankings are ordered by the same stored pfp_global_rank values the site displays.
    """
    return (
        CharacterRanking.objects.filter(pfp_global_rank__gt=0)
        .select_related("player", "character")
        .order_by("pfp_global_rank")
    )


def serialize_pfp_ranking(ranking: CharacterRanking) -> dict:
    """Serialize a CharacterRanking into the public PFP leaderboard shape."""
    return {
        "global_rank": ranking.pfp_global_rank,
        "pfp_score": round(ranking.pfp_score, 2),
        "percentile_score": round(ranking.pfp_percentile_score, 2),
        "vote_score": round(ranking.pfp_vote_score, 2),
        "competition_score": round(ranking.pfp_competition_score, 2),
        "champion_bonus": round(ranking.pfp_champion_bonus, 2),
        "character_rank": ranking.pfp_character_rank,
        "all_time_votes": ranking.all_time_votes,
        "player_nickname": ranking.player.nickname,
        "player_username": ranking.player.username or None,
        "player_slug": ranking.player.slug,
        "player_name_burning": ranking.player.name_burning,
        "player_name_smoke": ranking.player.name_smoke,
        "player_name_glitch": ranking.player.name_glitch,
        "character_name": ranking.character.name,
        "character_slug": ranking.character.slug,
        "character_side": ranking.character.side,
    }


def get_pfp_leaderboard_entries(limit: int | None = None) -> list[dict]:
    """Return serialized PFP rankings in website order."""
    queryset = get_pfp_leaderboard_queryset()
    if limit is not None:
        queryset = queryset[: max(0, int(limit))]
    return [serialize_pfp_ranking(ranking) for ranking in queryset]


def recalculate_all_pfp_scores():
    characters = list(
        Character.objects.annotate(
            total_players=Count("rankings"),
        )
    )
    largest_character_size = max((character.total_players for character in characters), default=0)
    global_max_votes = (
        CharacterRanking.objects.aggregate(max_votes=Max("all_time_votes"))["max_votes"] or 0
    )

    metrics_by_ranking_id = {}

    for character in characters:
        if character.total_players <= 0:
            continue

        rankings = list(
            character.rankings.select_related("player").order_by("-votes", "created_at")
        )

        for rank, ranking in enumerate(rankings, start=1):
            metrics = calculate_pfp_metrics(
                rank=rank,
                total_players=character.total_players,
                votes=ranking.all_time_votes,
                max_votes=global_max_votes,
                largest_character_size=largest_character_size,
            )
            if metrics is None:
                continue
            metrics.ranking_id = ranking.id
            metrics_by_ranking_id[ranking.id] = metrics

    sorted_metrics = sorted(metrics_by_ranking_id.values(), key=_pfp_sort_key)

    rankings = CharacterRanking.objects.filter(id__in=metrics_by_ranking_id.keys())
    ranking_map = {ranking.id: ranking for ranking in rankings}

    to_update = []
    for global_rank, metrics in enumerate(sorted_metrics, start=1):
        ranking = ranking_map.get(metrics.ranking_id)
        if ranking is None:
            continue
        ranking.pfp_score = metrics.pfp_score
        ranking.pfp_percentile_score = metrics.percentile_score
        ranking.pfp_vote_score = metrics.vote_score
        ranking.pfp_competition_score = metrics.competition_score
        ranking.pfp_champion_bonus = metrics.champion_bonus
        ranking.pfp_character_rank = metrics.rank
        ranking.pfp_global_rank = global_rank
        to_update.append(ranking)

    if to_update:
        CharacterRanking.objects.bulk_update(
            to_update,
            [
                "pfp_score",
                "pfp_percentile_score",
                "pfp_vote_score",
                "pfp_competition_score",
                "pfp_champion_bonus",
                "pfp_character_rank",
                "pfp_global_rank",
            ],
        )

    CharacterRanking.objects.exclude(id__in=metrics_by_ranking_id.keys()).update(
        pfp_score=0,
        pfp_percentile_score=0,
        pfp_vote_score=0,
        pfp_competition_score=0,
        pfp_champion_bonus=0,
        pfp_character_rank=0,
        pfp_global_rank=0,
    )

    return len(to_update)
