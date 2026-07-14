"""Reusable Discord webhook client with retries and safe logging."""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_discord_webhook_url(setting_name: str = "DISCORD_WEBHOOK_URL") -> str:
    """Return configured webhook URL for `setting_name`, or empty if missing/invalid."""
    raw = getattr(settings, setting_name, None) or ""
    url = str(raw).strip()
    if not url:
        return ""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        logger.warning(
            "Discord webhook setting %s is configured but invalid; skipping send.",
            setting_name,
        )
        return ""

    if "discord.com/api/webhooks/" not in url and "discordapp.com/api/webhooks/" not in url:
        logger.warning(
            "Discord webhook setting %s does not look like a Discord webhook; skipping send.",
            setting_name,
        )
        return ""

    return url


def _request_timeout() -> float:
    return float(getattr(settings, "DISCORD_WEBHOOK_TIMEOUT_SECONDS", 8))


def _max_retries() -> int:
    return int(getattr(settings, "DISCORD_WEBHOOK_MAX_RETRIES", 3))


def _backoff_multiplier() -> float:
    return float(getattr(settings, "DISCORD_WEBHOOK_BACKOFF_MULTIPLIER", 2.0))


def send_discord_webhook_payload(
    payload: dict[str, Any],
    *,
    setting_name: str = "DISCORD_WEBHOOK_URL",
) -> bool:
    """
    POST a Discord webhook JSON payload with retries and exponential backoff.

    Returns True on HTTP 2xx. Never raises. Never logs the webhook URL.
    """
    webhook_url = get_discord_webhook_url(setting_name)
    if not webhook_url:
        logger.warning(
            "Discord webhook %s missing or invalid; notification skipped.",
            setting_name,
        )
        return False

    timeout = _request_timeout()
    max_retries = max(1, _max_retries())
    backoff = _backoff_multiplier()
    last_error: str | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(webhook_url, json=payload, timeout=timeout)
            if 200 <= response.status_code < 300:
                logger.info(
                    "Discord webhook send succeeded via %s (attempt %s/%s, status=%s).",
                    setting_name,
                    attempt,
                    max_retries,
                    response.status_code,
                )
                return True

            body = (response.text or "")[:500]
            last_error = f"status={response.status_code} body={body}"
            logger.error(
                "Discord webhook send failed via %s (attempt %s/%s): %s",
                setting_name,
                attempt,
                max_retries,
                last_error,
            )
        except requests.RequestException as exc:
            last_error = exc.__class__.__name__
            logger.error(
                "Discord webhook request error via %s (attempt %s/%s): %s",
                setting_name,
                attempt,
                max_retries,
                last_error,
            )

        if attempt < max_retries:
            sleep_for = backoff ** (attempt - 1)
            time.sleep(sleep_for)

    logger.error(
        "Discord webhook send via %s exhausted retries. Last error: %s",
        setting_name,
        last_error,
    )
    return False


def send_discord_embeds(
    embeds: list[dict[str, Any]],
    *,
    content: str | None = None,
    setting_name: str = "DISCORD_WEBHOOK_URL",
) -> bool:
    """Send one or more Discord embeds via webhook."""
    payload: dict[str, Any] = {"embeds": embeds}
    if content:
        payload["content"] = content
    return send_discord_webhook_payload(payload, setting_name=setting_name)


def send_discord_content(
    content: str,
    *,
    setting_name: str = "DISCORD_WEBHOOK_URL",
) -> bool:
    """Send a plain-text Discord webhook message."""
    return send_discord_webhook_payload({"content": content}, setting_name=setting_name)
