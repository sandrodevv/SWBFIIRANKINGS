"""Background scheduler for automated Discord notifications."""

from __future__ import annotations

import logging
import os
import sys
import threading

from django.conf import settings

logger = logging.getLogger(__name__)

_scheduler_started = False
_scheduler_lock = threading.Lock()


def run_scheduled_discord_jobs() -> None:
    """
    Execute due Discord notification jobs.

    Safe to call frequently; individual jobs enforce their own idempotency.
    Never raises.
    """
    try:
        from apps.rankings.services.pfp_discord import send_pfp_ending_soon_notification

        result = send_pfp_ending_soon_notification(force=False)
        if result not in {"skipped_outside_window", "skipped_duplicate"}:
            logger.info("Scheduled Discord job finished with status=%s", result)
    except Exception:
        logger.exception("Scheduled Discord jobs failed unexpectedly.")


def _scheduler_loop(interval_seconds: int, stop_event: threading.Event) -> None:
    logger.info(
        "Discord notification scheduler started (interval=%ss).",
        interval_seconds,
    )
    # Run once shortly after boot in case the process starts inside the window.
    run_scheduled_discord_jobs()
    while not stop_event.wait(interval_seconds):
        run_scheduled_discord_jobs()


def should_start_background_scheduler() -> bool:
    """Decide whether this process should own the background scheduler thread."""
    if not getattr(settings, "DISCORD_SCHEDULER_ENABLED", True):
        return False

    # Avoid starting twice under Django's autoreloader parent process.
    if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
        return False

    # Skip common one-off management commands where a long-lived thread is useless.
    skip_commands = {
        "migrate",
        "makemigrations",
        "collectstatic",
        "test",
        "shell",
        "createsuperuser",
        "check",
        "send_pfp_ending_webhook",
    }
    if len(sys.argv) > 1 and sys.argv[1] in skip_commands:
        return False

    return True


def start_discord_scheduler() -> threading.Event | None:
    """
    Start a daemon thread that periodically runs Discord notification jobs.

    Returns the stop event when started, otherwise None.
    Idempotent within a single process.
    """
    global _scheduler_started

    with _scheduler_lock:
        if _scheduler_started:
            return None
        if not should_start_background_scheduler():
            return None

        interval = max(15, int(getattr(settings, "DISCORD_SCHEDULER_INTERVAL_SECONDS", 60)))
        stop_event = threading.Event()
        thread = threading.Thread(
            target=_scheduler_loop,
            args=(interval, stop_event),
            name="discord-notification-scheduler",
            daemon=True,
        )
        thread.start()
        _scheduler_started = True
        return stop_event
