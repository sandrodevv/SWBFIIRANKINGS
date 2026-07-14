from django.db.models import Q

from apps.rankings.models import Duelist, DuelistVoteRecord
from apps.rankings.services.voting import get_vote_cooldown
from apps.rankings.services.weekly_reset import (
    ensure_current_period,
    get_period_end,
)

DUELIST_REGIONS = (Duelist.REGION_EU, Duelist.REGION_US, Duelist.REGION_AU)


def get_active_duelist_vote_record(ip_hash, voter_hash, region):
    period = ensure_current_period()
    return (
        DuelistVoteRecord.objects.filter(
            voted_at__gte=period.started_at,
            duelist__region=region,
        )
        .filter(Q(ip_hash=ip_hash) | Q(voter_hash=voter_hash))
        .select_related("duelist__player")
        .order_by("-voted_at")
        .first()
    )


def _status_for_record(period, record):
    next_vote_at = get_period_end(period)
    if not record:
        return {
            "can_vote": True,
            "voted_at": None,
            "next_vote_at": None,
            "cooldown_days": get_vote_cooldown().days,
            "message": None,
            "last_voted_player": None,
            "last_voted_username": None,
            "last_voted_name_burning": None,
            "last_voted_name_smoke": None,
            "last_voted_name_glitch": None,
            "period_ends_at": next_vote_at.isoformat(),
        }

    player = record.duelist.player
    region_label = record.duelist.get_region_display()
    return {
        "can_vote": False,
        "voted_at": record.voted_at.isoformat(),
        "next_vote_at": next_vote_at.isoformat(),
        "cooldown_days": get_vote_cooldown().days,
        "message": (
            f"You already voted in {region_label} this week. "
            f"You can vote again in that region when rankings reset "
            f"on {next_vote_at.strftime('%b %d, %Y %H:%M UTC')}."
        ),
        "last_voted_player": player.nickname,
        "last_voted_username": player.username or None,
        "last_voted_name_burning": player.name_burning,
        "last_voted_name_smoke": player.name_smoke,
        "last_voted_name_glitch": player.name_glitch,
        "period_ends_at": next_vote_at.isoformat(),
    }


def get_duelist_vote_status(ip_hash, voter_hash, region):
    period = ensure_current_period()
    record = get_active_duelist_vote_record(ip_hash, voter_hash, region)
    status = _status_for_record(period, record)
    status["region"] = region
    return status


def get_all_duelist_vote_statuses(ip_hash, voter_hash):
    period = ensure_current_period()
    regions = {}
    for region in DUELIST_REGIONS:
        record = get_active_duelist_vote_record(ip_hash, voter_hash, region)
        status = _status_for_record(period, record)
        status["region"] = region
        regions[region] = status
    return {
        "regions": regions,
        "period_ends_at": get_period_end(period).isoformat(),
        "cooldown_days": get_vote_cooldown().days,
    }


def record_duelist_vote(duelist, ip_hash, voter_hash):
    return DuelistVoteRecord.objects.create(
        duelist=duelist,
        ip_hash=ip_hash,
        voter_hash=voter_hash,
    )
