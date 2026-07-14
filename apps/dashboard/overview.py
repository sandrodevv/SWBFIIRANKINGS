from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.dashboard.forms import players_needing_assignment
from apps.dashboard.models import ModeratorLoginLog
from apps.rankings.models import (
    CharacterRanking,
    Duelist,
    DuelistVoteRecord,
    Player,
    VoteRecord,
)
from apps.rankings.services.weekly_reset import get_current_period, get_period_end


def _name_effects_overview():
    players = list(
        Player.objects.filter(
            Q(name_burning=True) | Q(name_smoke=True) | Q(name_glitch=True)
        )
        .order_by("nickname")
        .values("nickname", "slug", "name_burning", "name_smoke", "name_glitch")
    )
    return {
        "any": len(players),
        "burning": sum(1 for player in players if player["name_burning"]),
        "smoke": sum(1 for player in players if player["name_smoke"]),
        "glitch": sum(1 for player in players if player["name_glitch"]),
        "players": players,
    }


def get_admin_overview(*, include_details=True):
    period = get_current_period()
    period_end = get_period_end(period)
    now = timezone.now()
    seconds_left = max(0, int((period_end - now).total_seconds()))

    ranking_votes = CharacterRanking.objects.aggregate(
        weekly=Sum("votes"),
        last_week=Sum("last_week_votes"),
        all_time=Sum("all_time_votes"),
    )
    duelist_votes = Duelist.objects.aggregate(
        weekly=Sum("votes"),
        last_week=Sum("last_week_votes"),
        all_time=Sum("all_time_votes"),
    )

    incomplete = players_needing_assignment()
    incomplete_count = incomplete.count()

    duelist_by_region = {
        row["region"]: row["n"]
        for row in Duelist.objects.values("region").annotate(n=Count("id"))
    }

    ranking_votes_this_period = VoteRecord.objects.filter(
        voted_at__gte=period.started_at
    ).count()
    duelist_votes_this_period = DuelistVoteRecord.objects.filter(
        voted_at__gte=period.started_at
    ).count()

    overview = {
        "period": {
            "started_at": period.started_at,
            "ends_at": period_end,
            "seconds_left": seconds_left,
            "days_left": seconds_left // 86400,
            "hours_left": (seconds_left % 86400) // 3600,
        },
        "counts": {
            "players": Player.objects.count(),
            "rankings": CharacterRanking.objects.count(),
            "duelists": Duelist.objects.count(),
            "duelists_eu": duelist_by_region.get(Duelist.REGION_EU, 0),
            "duelists_us": duelist_by_region.get(Duelist.REGION_US, 0),
            "duelists_au": duelist_by_region.get(Duelist.REGION_AU, 0),
            "incomplete_assignments": incomplete_count,
            "votes_this_period": ranking_votes_this_period,
            "duelist_votes_this_period": duelist_votes_this_period,
            "total_votes_this_period": ranking_votes_this_period + duelist_votes_this_period,
        },
        "votes": {
            "ranking_weekly": ranking_votes["weekly"] or 0,
            "ranking_last_week": ranking_votes["last_week"] or 0,
            "ranking_all_time": ranking_votes["all_time"] or 0,
            "duelist_weekly": duelist_votes["weekly"] or 0,
            "duelist_last_week": duelist_votes["last_week"] or 0,
            "duelist_all_time": duelist_votes["all_time"] or 0,
        },
        "name_effects": _name_effects_overview(),
    }

    if not include_details:
        return overview

    overview.update(
        {
            "top_players": list(
                Player.objects.order_by("-all_time_votes", "nickname")[:8].values(
                    "nickname",
                    "slug",
                    "all_time_votes",
                )
            ),
            "top_weekly_rankings": list(
                CharacterRanking.objects.select_related("player", "character")
                .order_by("-votes", "created_at")[:8]
            ),
            "top_duelists": list(
                Duelist.objects.select_related("player", "character")
                .order_by("-votes", "created_at")[:8]
            ),
            "recent_votes": list(
                VoteRecord.objects.select_related(
                    "ranking__player",
                    "character",
                ).order_by("-voted_at")[:12]
            ),
            "recent_duelist_votes": list(
                DuelistVoteRecord.objects.select_related(
                    "duelist__player",
                    "duelist__character",
                ).order_by("-voted_at")[:8]
            ),
            "recent_logins": list(
                ModeratorLoginLog.objects.select_related("user").order_by("-logged_in_at")[:8]
            ),
            "incomplete_players": list(incomplete.select_related("duelist")[:12]),
        }
    )
    return overview
