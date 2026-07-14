"""Discord notification helpers that compose webhook payloads."""

from __future__ import annotations

import logging

from django.conf import settings
from django.utils import timezone

from apps.characters.models import Character
from apps.rankings.services.discord_webhook import send_discord_content, send_discord_embeds

logger = logging.getLogger(__name__)


def _registration_embed_color() -> int:
    """Green embed sidebar color for registration notifications."""
    return int(getattr(settings, "DISCORD_REGISTRATION_EMBED_COLOR", 0x57F287))


def notify_player_registration(player) -> None:
    """Notify Discord after a player has been created/updated with assignments."""
    rankings = list(player.rankings.select_related("character"))
    hero = next((r for r in rankings if r.character.side == Character.SIDE_HERO), None)
    villain = next((r for r in rankings if r.character.side == Character.SIDE_VILLAIN), None)
    has_duelist = hasattr(player, "duelist")

    fields = [
        {
            "name": "Hero",
            "value": hero.character.name if hero else "No",
            "inline": True,
        },
        {
            "name": "Villain",
            "value": villain.character.name if villain else "No",
            "inline": True,
        },
    ]

    if has_duelist:
        duelist = player.duelist
        fields.append(
            {
                "name": "Duelist",
                "value": f"{duelist.character.name} ({duelist.get_region_display()})",
                "inline": True,
            }
        )
    else:
        fields.append(
            {
                "name": "Duelist",
                "value": "No",
                "inline": True,
            }
        )

    if player.username:
        fields.append(
            {
                "name": "Known as",
                "value": player.username,
                "inline": False,
            }
        )

    embed = {
        "title": f"🟢 {player.nickname} just got registered!",
        "color": _registration_embed_color(),
        "fields": fields,
        "timestamp": timezone.now().isoformat(),
    }

    ok = send_discord_embeds(
        [embed],
        setting_name="DISCORD_RANKED_PLAYER_WEBHOOK_URL",
    )
    if not ok:
        logger.warning("Player registration Discord notification was not delivered.")


# Backwards-compatible alias used by older imports.
def send_discord_notification(message: str) -> None:
    send_discord_content(message)
