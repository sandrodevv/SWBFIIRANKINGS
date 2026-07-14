"""Weekly voting period helpers.

Periods are pinned to a fixed UTC schedule (default: every Sunday 22:00 UTC),
not to “7 days from whenever the last reset happened.”
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.rankings.services.pfp import recalculate_all_pfp_scores
from apps.rankings.models import CharacterRanking, Duelist, WeeklyVotePeriod


def get_period_duration() -> timedelta:
    days = getattr(settings, "VOTE_COOLDOWN_DAYS", 7)
    return timedelta(days=days)


def get_vote_reset_weekday() -> int:
    """Python weekday: Monday=0 ... Sunday=6. Default Sunday."""
    return int(getattr(settings, "VOTE_RESET_WEEKDAY", 6))


def get_vote_reset_hour_utc() -> int:
    return int(getattr(settings, "VOTE_RESET_HOUR_UTC", 22))


def get_vote_reset_minute_utc() -> int:
    return int(getattr(settings, "VOTE_RESET_MINUTE_UTC", 0))


def _as_utc(dt: datetime) -> datetime:
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, dt_timezone.utc)
    return dt.astimezone(dt_timezone.utc)


def get_scheduled_period_start(at: datetime | None = None) -> datetime:
    """
    Return the current period's start: the most recent reset boundary
    (e.g. Sunday 22:00 UTC) that is <= `at`.
    """
    at = _as_utc(at or timezone.now())
    weekday = get_vote_reset_weekday()
    hour = get_vote_reset_hour_utc()
    minute = get_vote_reset_minute_utc()

    days_since = (at.weekday() - weekday) % 7
    boundary_day = at - timedelta(days=days_since)
    boundary = boundary_day.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )
    if at < boundary:
        boundary -= get_period_duration()
    return boundary


def get_current_period():
    return WeeklyVotePeriod.get_singleton()


def get_period_end(period=None) -> datetime:
    """Return when the given (or current) period ends on the fixed schedule."""
    period = period or get_current_period()
    start = get_scheduled_period_start(period.started_at)
    if _same_boundary(period.started_at, start):
        start = _as_utc(period.started_at).replace(second=0, microsecond=0)
    return start + get_period_duration()


def period_has_expired(period=None) -> bool:
    period = period or get_current_period()
    return timezone.now() >= get_period_end(period)


def snapshot_and_reset_weekly_votes() -> None:
    """Save current weekly votes as last_week_votes, then zero the current week."""
    CharacterRanking.objects.update(last_week_votes=F("votes"), votes=0)
    Duelist.objects.update(last_week_votes=F("votes"), votes=0)


def _same_boundary(left: datetime, right: datetime) -> bool:
    return abs((_as_utc(left) - _as_utc(right)).total_seconds()) < 1


@transaction.atomic
def ensure_current_period():
    """
    Ensure WeeklyVotePeriod matches the current Sunday 22:00 UTC window.

    - If the schedule has advanced → snapshot/reset votes and move started_at.
    - If started_at is only slightly off-grid within the same week → snap without
      wiping votes (safe migration/align).
    """
    now = timezone.now()
    scheduled_start = get_scheduled_period_start(now)
    period = WeeklyVotePeriod.objects.select_for_update().get_or_create(
        pk=1,
        defaults={"started_at": scheduled_start},
    )[0]

    if _same_boundary(period.started_at, scheduled_start):
        if period.started_at != scheduled_start:
            period.started_at = scheduled_start
            period.save(update_fields=["started_at"])
        return period

    if _as_utc(period.started_at) < scheduled_start:
        # Align-only when still inside the same weekly window as the new start.
        previous_boundary = scheduled_start - get_period_duration()
        if _as_utc(period.started_at) > previous_boundary:
            period.started_at = scheduled_start
            period.save(update_fields=["started_at"])
            return period

        snapshot_and_reset_weekly_votes()
        period.started_at = scheduled_start
        period.save(update_fields=["started_at"])
        recalculate_all_pfp_scores()
        return period

    # started_at is somehow ahead of the schedule — snap back without reset.
    period.started_at = scheduled_start
    period.save(update_fields=["started_at"])
    return period


@transaction.atomic
def reset_weekly_votes():
    """Force a weekly reset and align started_at to the current schedule boundary."""
    scheduled_start = get_scheduled_period_start()
    period = WeeklyVotePeriod.objects.select_for_update().get_or_create(
        pk=1,
        defaults={"started_at": scheduled_start},
    )[0]
    snapshot_and_reset_weekly_votes()
    period.started_at = scheduled_start
    period.save(update_fields=["started_at"])
    recalculate_all_pfp_scores()
    return period


def align_period_to_schedule(*, reset_votes: bool = False):
    """
    Align the singleton period to the current schedule boundary.

    By default does not wipe votes (for one-time schedule adoption).
    """
    scheduled_start = get_scheduled_period_start()
    with transaction.atomic():
        period = WeeklyVotePeriod.objects.select_for_update().get_or_create(
            pk=1,
            defaults={"started_at": scheduled_start},
        )[0]
        if reset_votes:
            snapshot_and_reset_weekly_votes()
            recalculate_all_pfp_scores()
        if not _same_boundary(period.started_at, scheduled_start):
            period.started_at = scheduled_start
            period.save(update_fields=["started_at"])
        return period
