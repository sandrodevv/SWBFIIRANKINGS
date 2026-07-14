"""Discord notifications for regional duelist weekly winners on period reset."""

from __future__ import annotations

import logging
from datetime import datetime, timezone as dt_timezone
from typing import Any

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.rankings.models import DiscordNotificationLog, Duelist
from apps.rankings.services.discord_webhook import send_discord_embeds

logger = logging.getLogger(__name__)

RANK_MEDALS = {
    1: "🥇",
    2: "🥈",
    3: "🥉",
}

# region code -> Discord wiring
REGION_WEBHOOK_CONFIG = {
    Duelist.REGION_EU: {
        "label": "EU",
        "webhook_setting": "DISCORD_EU_DUELIST_WEBHOOK_URL",
        "notification_type": DiscordNotificationLog.TYPE_EU_DUELIST_WEEKLY_WINNERS,
        "top_n_setting": "EU_DUELIST_WEBHOOK_TOP_N",
        "color_setting": "EU_DUELIST_WEBHOOK_EMBED_COLOR",
        "default_color": 0x3B82F6,
    },
    Duelist.REGION_US: {
        "label": "US",
        "webhook_setting": "DISCORD_US_DUELIST_WEBHOOK_URL",
        "notification_type": DiscordNotificationLog.TYPE_US_DUELIST_WEEKLY_WINNERS,
        "top_n_setting": "US_DUELIST_WEBHOOK_TOP_N",
        "color_setting": "US_DUELIST_WEBHOOK_EMBED_COLOR",
        "default_color": 0xEF4444,
    },
    Duelist.REGION_AU: {
        "label": "AU",
        "webhook_setting": "DISCORD_AU_DUELIST_WEBHOOK_URL",
        "notification_type": DiscordNotificationLog.TYPE_AU_DUELIST_WEEKLY_WINNERS,
        "top_n_setting": "AU_DUELIST_WEBHOOK_TOP_N",
        "color_setting": "AU_DUELIST_WEBHOOK_EMBED_COLOR",
        "default_color": 0x22C55E,
    },
}


def _top_n(region: str) -> int:
    config = REGION_WEBHOOK_CONFIG[region]
    return max(1, int(getattr(settings, config["top_n_setting"], 16)))


def _embed_color(region: str) -> int:
    config = REGION_WEBHOOK_CONFIG[region]
    return int(getattr(settings, config["color_setting"], config["default_color"]))


def _rank_label(rank: int) -> str:
    medal = RANK_MEDALS.get(rank)
    if medal:
        return f"{medal} #{rank}"
    return f"#{rank}"


def get_duelist_last_week_top(
    region: str,
    limit: int | None = None,
) -> list[Duelist]:
    """Return top duelists for a region ranked by previous week's votes."""
    limit = limit if limit is not None else _top_n(region)
    return list(
        Duelist.objects.filter(region=region)
        .select_related("player", "character")
        .order_by("-last_week_votes", "created_at")[:limit]
    )


def build_duelist_winners_embed(
    duelists: list[Duelist],
    *,
    region: str,
    period_started_at: datetime | None = None,
) -> dict[str, Any]:
    """Build a Discord embed for previous-week regional duelist winners."""
    label = REGION_WEBHOOK_CONFIG[region]["label"]
    description = f"Previous week's top {label} duelists after the weekly reset."
    if period_started_at is not None:
        description += f"\nNew period started: {_as_display_date(period_started_at)}"

    lines: list[str] = []
    for index, duelist in enumerate(duelists, start=1):
        nickname = duelist.player.nickname
        character = duelist.character.name
        votes = duelist.last_week_votes
        lines.append(
            f"{_rank_label(index)} **{nickname}** — {character} · **{votes}** votes"
        )

    if not lines:
        lines.append(f"_No {label} duelist votes recorded last week._")

    body = "\n".join(lines)
    if len(body) > 3500:
        body = "\n".join(lines[:16])

    return {
        "title": f"⚔️ {label} Duelist Weekly Winners",
        "description": f"{description}\n\n{body}",
        "color": _embed_color(region),
        "timestamp": timezone.now().isoformat(),
        "footer": {
            "text": f"Top {_top_n(region)} · {label} region",
        },
    }


def _as_display_date(value: datetime) -> str:
    aware = value
    if timezone.is_naive(aware):
        aware = timezone.make_aware(aware, dt_timezone.utc)
    return timezone.localtime(aware).strftime("%Y-%m-%d %H:%M %Z")


def _claim_notification_slot(
    period_started_at: datetime,
    *,
    notification_type: str,
    region_label: str,
    force: bool = False,
) -> DiscordNotificationLog | None:
    """Claim the unique regional winners slot for this voting period."""
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
                    "%s duelist Discord notification claim lost a race; skipping.",
                    region_label,
                )
                return None

        if existing.status == DiscordNotificationLog.STATUS_SENT and not force:
            logger.info(
                "%s duelist winners already sent for period starting %s; skipping.",
                region_label,
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
                "%s duelist winners already claimed/pending for period %s; skipping.",
                region_label,
                period_started_at.isoformat(),
            )
            return None

        existing.status = DiscordNotificationLog.STATUS_PENDING
        existing.detail = "Retrying send" if force else "Claimed for send"
        existing.save(update_fields=["status", "detail", "updated_at"])
        return existing


def send_duelist_weekly_winners_notification(
    region: str,
    *,
    period_started_at: datetime | None = None,
    force: bool = False,
) -> str:
    """
    Send top duelists from last_week_votes for a region after weekly reset.

    Idempotent per (region notification type, period_started_at). Never raises.
    """
    config = REGION_WEBHOOK_CONFIG.get(region)
    if config is None:
        logger.error("Unsupported duelist webhook region: %s", region)
        return "error"

    label = config["label"]
    try:
        from apps.rankings.services.weekly_reset import get_current_period

        period_started_at = period_started_at or get_current_period().started_at
        claim = _claim_notification_slot(
            period_started_at,
            notification_type=config["notification_type"],
            region_label=label,
            force=force,
        )
        if claim is None:
            return "skipped_duplicate"

        duelists = get_duelist_last_week_top(region)
        embed = build_duelist_winners_embed(
            duelists,
            region=region,
            period_started_at=period_started_at,
        )
        ok = send_discord_embeds(
            [embed],
            setting_name=config["webhook_setting"],
        )

        if ok:
            claim.status = DiscordNotificationLog.STATUS_SENT
            claim.entry_count = len(duelists)
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
                "%s duelist weekly winners Discord notification sent (%s entries).",
                label,
                len(duelists),
            )
            return "sent"

        claim.status = DiscordNotificationLog.STATUS_FAILED
        claim.entry_count = len(duelists)
        claim.detail = "Webhook delivery failed"
        claim.save(
            update_fields=["status", "entry_count", "detail", "updated_at"]
        )
        logger.error("%s duelist weekly winners Discord notification failed.", label)
        return "failed"
    except Exception:
        logger.exception(
            "Unexpected error while sending %s duelist Discord notification.",
            label,
        )
        return "error"


def send_all_regional_duelist_weekly_winners(
    *,
    period_started_at: datetime | None = None,
    force: bool = False,
) -> dict[str, str]:
    """Send weekly winners for every configured region."""
    results: dict[str, str] = {}
    for region in REGION_WEBHOOK_CONFIG:
        results[region] = send_duelist_weekly_winners_notification(
            region,
            period_started_at=period_started_at,
            force=force,
        )
    return results


# Backwards-compatible EU helpers
def get_eu_duelist_last_week_top(limit: int | None = None) -> list[Duelist]:
    return get_duelist_last_week_top(Duelist.REGION_EU, limit=limit)


def build_eu_duelist_winners_embed(
    duelists: list[Duelist],
    *,
    period_started_at: datetime | None = None,
) -> dict[str, Any]:
    return build_duelist_winners_embed(
        duelists,
        region=Duelist.REGION_EU,
        period_started_at=period_started_at,
    )


def send_eu_duelist_weekly_winners_notification(
    *,
    period_started_at: datetime | None = None,
    force: bool = False,
) -> str:
    return send_duelist_weekly_winners_notification(
        Duelist.REGION_EU,
        period_started_at=period_started_at,
        force=force,
    )


def send_us_duelist_weekly_winners_notification(
    *,
    period_started_at: datetime | None = None,
    force: bool = False,
) -> str:
    return send_duelist_weekly_winners_notification(
        Duelist.REGION_US,
        period_started_at=period_started_at,
        force=force,
    )


def send_au_duelist_weekly_winners_notification(
    *,
    period_started_at: datetime | None = None,
    force: bool = False,
) -> str:
    return send_duelist_weekly_winners_notification(
        Duelist.REGION_AU,
        period_started_at=period_started_at,
        force=force,
    )
