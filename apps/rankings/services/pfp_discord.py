"""Build and send the weekly PFP-ending Discord embed."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.rankings.models import DiscordNotificationLog
from apps.rankings.services.discord_webhook import send_discord_embeds
from apps.rankings.services.pfp import get_pfp_leaderboard_entries
from apps.rankings.services.weekly_reset import get_current_period, get_period_end

logger = logging.getLogger(__name__)

RANK_MEDALS = {
    1: "🥇",
    2: "🥈",
    3: "🥉",
}


def _top_n() -> int:
    return max(1, int(getattr(settings, "PFP_WEBHOOK_TOP_N", 15)))


def _embed_color() -> int:
    return int(getattr(settings, "PFP_WEBHOOK_EMBED_COLOR", 0xD4A843))


def _rank_label(rank: int) -> str:
    medal = RANK_MEDALS.get(rank)
    if medal:
        return f"{medal} #{rank}"
    return f"#{rank}"


def build_pfp_rankings_embed(
    entries: list[dict[str, Any]],
    *,
    period_ends_at: datetime | None = None,
) -> dict[str, Any]:
    """Build a Discord embed payload from serialized PFP leaderboard entries."""
    description = (
        "The current Pound-for-Pound rankings."
    )
    if period_ends_at is not None:
        description += f"\nPublished: {timezone.now().strftime('%Y-%m-%d')}"

    fields: list[dict[str, Any]] = []
    for entry in entries:
        rank = int(entry.get("global_rank") or 0)
        player = entry.get("player_nickname") or "Unknown"
        character = entry.get("character_name") or "Unknown"
        score = entry.get("pfp_score")
        character_rank = entry.get("character_rank")

        value_lines = [
            f"**Player:** {player}",
            f"**Character:** {character}",
            f"**PFP Score:** {score}",
        ]
        if character_rank:
            value_lines.append(f"**Character Rank:** #{character_rank}")
        

        fields.append(
            {
                "name": f"{_rank_label(rank)} {player}",
                "value": "\n".join(value_lines),
                "inline": False,
            }
        )

    if not fields:
        fields.append(
            {
                "name": "No rankings yet",
                "value": "PFP scores have not been calculated for this period.",
                "inline": False,
            }
        )

    # Discord allows max 25 fields per embed.
    fields = fields[:25]

    return {
        "title": "🏆 Current PFP Rankings",
        "description": description,
        "color": _embed_color(),
        "fields": fields,
        "timestamp": timezone.now().isoformat(),
        "footer": {
            "text": "Vote now to make changes!",
        },
    }


def _claim_notification_slot(
    period_started_at: datetime,
    *,
    force: bool = False,
) -> DiscordNotificationLog | None:
    """
    Claim the unique notification slot for this voting period.

    Returns a log row to proceed with, or None if already successfully sent
    (or another worker holds a fresh pending claim).
    """
    notification_type = DiscordNotificationLog.TYPE_PFP_WEEKLY_ENDING
    pending_ttl_seconds = int(
        getattr(settings, "PFP_WEBHOOK_PENDING_CLAIM_TTL_SECONDS", 300)
    )

    with transaction.atomic():
        existing = (
            DiscordNotificationLog.objects.select_for_update()
            .filter(
                notification_type=notification_type,
                period_started_at=period_started_at,
            )
            .first()
        )

        if existing is None:
            try:
                return DiscordNotificationLog.objects.create(
                    notification_type=notification_type,
                    period_started_at=period_started_at,
                    status=DiscordNotificationLog.STATUS_PENDING,
                )
            except IntegrityError:
                logger.info(
                    "PFP Discord notification claim lost a race; skipping duplicate."
                )
                return None

        if existing.status == DiscordNotificationLog.STATUS_SENT and not force:
            logger.info(
                "PFP Discord notification already sent for period starting %s; skipping.",
                period_started_at.isoformat(),
            )
            return None

        if (
            existing.status == DiscordNotificationLog.STATUS_PENDING
            and not force
            and (timezone.now() - existing.updated_at).total_seconds()
            < pending_ttl_seconds
        ):
            logger.info(
                "PFP Discord notification already claimed/pending for period starting %s; skipping.",
                period_started_at.isoformat(),
            )
            return None

        existing.status = DiscordNotificationLog.STATUS_PENDING
        existing.detail = "Retrying send" if force else "Claimed for send"
        existing.save(
            update_fields=["status", "detail", "updated_at"],
        )
        return existing


def is_within_pfp_webhook_window(now=None) -> bool:
    """True when current time is within the lead window before period end."""
    now = now or timezone.now()
    period = get_current_period()
    period_end = get_period_end(period)
    lead_minutes = int(getattr(settings, "PFP_WEBHOOK_LEAD_MINUTES", 10))
    window_start = period_end - timedelta(minutes=lead_minutes)
    return window_start <= now < period_end


def send_pfp_ending_soon_notification(*, force: bool = False) -> str:
    """
    Send current PFP rankings to Discord once per weekly voting period.

    Returns a short status string for logging/commands.
    Never raises.
    """
    try:
        period = get_current_period()
        period_end = get_period_end(period)
        now = timezone.now()

        if not force and not is_within_pfp_webhook_window(now):
            logger.debug(
                "Outside PFP webhook lead window (period ends %s); skipping.",
                period_end.isoformat(),
            )
            return "skipped_outside_window"

        claim = _claim_notification_slot(period.started_at, force=force)
        if claim is None:
            return "skipped_duplicate"

        entries = get_pfp_leaderboard_entries(limit=_top_n())
        embed = build_pfp_rankings_embed(entries, period_ends_at=period_end)
        ok = send_discord_embeds([embed])

        if ok:
            claim.status = DiscordNotificationLog.STATUS_SENT
            claim.entry_count = len(entries)
            claim.detail = "Delivered"
            claim.sent_at = timezone.now()
            claim.save(
                update_fields=[
                    "status",
                    "entry_count",
                    "detail",
                    "sent_at",
                    "updated_at",
                ]
            )
            logger.info(
                "PFP ending Discord notification sent (%s entries) for period %s.",
                len(entries),
                period.started_at.isoformat(),
            )
            return "sent"

        claim.status = DiscordNotificationLog.STATUS_FAILED
        claim.entry_count = len(entries)
        claim.detail = "Webhook delivery failed"
        claim.save(
            update_fields=["status", "entry_count", "detail", "updated_at"]
        )
        logger.error(
            "PFP ending Discord notification failed for period %s.",
            period.started_at.isoformat(),
        )
        return "failed"
    except Exception:
        logger.exception("Unexpected error while sending PFP Discord notification.")
        return "error"
