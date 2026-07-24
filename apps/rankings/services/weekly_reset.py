"""Weekly voting period helpers.

Periods are pinned to a fixed UTC schedule (default: every Sunday 22:00 UTC),
not to “7 days from whenever the last reset happened.”
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.characters.models import Character
from apps.rankings.services.pfp import recalculate_all_pfp_scores
from apps.rankings.models import CharacterRanking, Duelist, Player, WeeklyVotePeriod

logger = logging.getLogger(__name__)


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


def award_weekly_gold_medals() -> None:
    """
    Award permanent Hero/Villain gold medals from the finalized weekly snapshot.

    Call only after weekly votes have been copied into ``last_week_votes``.
    Each character's #1 (by last_week_votes, then created_at) earns +1 on that
    character's side. Counts are never decreased by vote resets.
    """
    hero_winner_ids: list[int] = []
    villain_winner_ids: list[int] = []

    for character in Character.objects.only("id", "side").iterator():
        top = (
            CharacterRanking.objects.filter(
                character_id=character.id,
                last_week_votes__gt=0,
            )
            .order_by("-last_week_votes", "created_at")
            .values_list("player_id", flat=True)
            .first()
        )
        if top is None:
            continue
        if character.side == Character.SIDE_HERO:
            hero_winner_ids.append(top)
        elif character.side == Character.SIDE_VILLAIN:
            villain_winner_ids.append(top)

    for player_id in hero_winner_ids:
        Player.objects.filter(pk=player_id).update(
            hero_gold_medals=F("hero_gold_medals") + 1
        )
    for player_id in villain_winner_ids:
        Player.objects.filter(pk=player_id).update(
            villain_gold_medals=F("villain_gold_medals") + 1
        )

    if hero_winner_ids or villain_winner_ids:
        logger.info(
            "Awarded weekly gold medals: hero=%s villain=%s",
            len(hero_winner_ids),
            len(villain_winner_ids),
        )


def snapshot_and_reset_weekly_votes() -> None:
    """Save current weekly votes as last_week_votes, then zero the current week."""
    CharacterRanking.objects.update(last_week_votes=F("votes"), votes=0)
    Duelist.objects.update(last_week_votes=F("votes"), votes=0)
    award_weekly_gold_medals()


def _schedule_duelist_winners_notifications(period_started_at: datetime) -> None:
    """Send previous-week regional tops + overall all-time after reset commits."""

    def _send() -> None:
        try:
            from apps.rankings.services.duelist_discord import (
                send_all_regional_duelist_weekly_winners,
                send_overall_alltime_duelist_notification,
            )

            results = send_all_regional_duelist_weekly_winners(
                period_started_at=period_started_at,
            )
            logger.info("Regional duelist weekly winners notification results=%s", results)

            overall_result = send_overall_alltime_duelist_notification(
                period_started_at=period_started_at,
            )
            logger.info(
                "Overall all-time duelist notification result=%s",
                overall_result,
            )
        except Exception:
            logger.exception(
                "Failed to queue/send duelist Discord notifications after weekly reset."
            )

    transaction.on_commit(_send)


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
        _schedule_duelist_winners_notifications(scheduled_start)
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
    _schedule_duelist_winners_notifications(scheduled_start)
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
            _schedule_duelist_winners_notifications(scheduled_start)
        if not _same_boundary(period.started_at, scheduled_start):
            period.started_at = scheduled_start
            period.save(update_fields=["started_at"])
        return period
