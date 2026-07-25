"""Fetch Google Analytics 4 traffic metrics for the administrator dashboard."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY = "dashboard:ga4:overview"
CACHE_TTL_SECONDS = 15 * 60


def _credentials_info():
    raw = (getattr(settings, "GA4_CREDENTIALS_JSON", "") or "").strip()
    if raw:
        return json.loads(raw)

    path = (getattr(settings, "GA4_CREDENTIALS_FILE", "") or "").strip()
    if path:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    return None


def is_analytics_configured() -> bool:
    property_id = (getattr(settings, "GA4_PROPERTY_ID", "") or "").strip()
    if not property_id:
        return False
    try:
        return _credentials_info() is not None
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return False


def _format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _metric_value(row, index: int = 0) -> float:
    try:
        return float(row.metric_values[index].value or 0)
    except (AttributeError, IndexError, TypeError, ValueError):
        return 0.0


def _dimension_value(row, index: int = 0) -> str:
    try:
        return (row.dimension_values[index].value or "").strip() or "(not set)"
    except (AttributeError, IndexError, TypeError):
        return "(not set)"


def _run_report(client, property_id: str, **kwargs):
    from google.analytics.data_v1beta.types import RunReportRequest

    return client.run_report(RunReportRequest(property=f"properties/{property_id}", **kwargs))


def _fetch_overview():
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy
    from google.oauth2 import service_account

    property_id = (settings.GA4_PROPERTY_ID or "").strip()
    credentials = service_account.Credentials.from_service_account_info(
        _credentials_info(),
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
    client = BetaAnalyticsDataClient(credentials=credentials)

    today = date.today()
    day_range = DateRange(start_date="1daysAgo", end_date="today")
    week_range = DateRange(start_date="7daysAgo", end_date="today")
    month_range = DateRange(start_date="30daysAgo", end_date="today")

    visitors = {}
    for key, date_range in (
        ("daily", day_range),
        ("weekly", week_range),
        ("monthly", month_range),
    ):
        response = _run_report(
            client,
            property_id,
            date_ranges=[date_range],
            metrics=[Metric(name="activeUsers")],
        )
        visitors[key] = int(_metric_value(response.rows[0])) if response.rows else 0

    audience = _run_report(
        client,
        property_id,
        date_ranges=[month_range],
        dimensions=[Dimension(name="newVsReturning")],
        metrics=[Metric(name="activeUsers")],
    )
    new_users = 0
    returning_users = 0
    for row in audience.rows:
        label = _dimension_value(row).lower()
        value = int(_metric_value(row))
        if "new" in label:
            new_users += value
        elif "returning" in label:
            returning_users += value

    countries_response = _run_report(
        client,
        property_id,
        date_ranges=[month_range],
        dimensions=[Dimension(name="country")],
        metrics=[Metric(name="activeUsers")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)],
        limit=10,
    )
    countries = [
        {"name": _dimension_value(row), "users": int(_metric_value(row))}
        for row in countries_response.rows
    ]

    devices_response = _run_report(
        client,
        property_id,
        date_ranges=[month_range],
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[Metric(name="activeUsers")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)],
    )
    devices = []
    for row in devices_response.rows:
        name = _dimension_value(row)
        label = {
            "desktop": "PC",
            "mobile": "Mobile",
            "tablet": "Tablet",
        }.get(name.lower(), name.title())
        devices.append({"name": label, "users": int(_metric_value(row))})

    pages_response = _run_report(
        client,
        property_id,
        date_ranges=[month_range],
        dimensions=[Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews"), Metric(name="averageSessionDuration")],
        order_bys=[
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
        ],
        limit=10,
    )
    pages = [
        {
            "path": _dimension_value(row),
            "views": int(_metric_value(row, 0)),
        }
        for row in pages_response.rows
    ]

    session_response = _run_report(
        client,
        property_id,
        date_ranges=[month_range],
        metrics=[
            Metric(name="averageSessionDuration"),
            Metric(name="sessions"),
            Metric(name="activeUsers"),
        ],
    )
    avg_seconds = _metric_value(session_response.rows[0]) if session_response.rows else 0.0
    sessions = int(_metric_value(session_response.rows[0], 1)) if session_response.rows else 0
    monthly_users = (
        int(_metric_value(session_response.rows[0], 2)) if session_response.rows else visitors["monthly"]
    )

    return {
        "configured": True,
        "error": None,
        "range_label": "Last 30 days",
        "as_of": today.isoformat(),
        "visitors": visitors,
        "new_users": new_users,
        "returning_users": returning_users,
        "countries": countries,
        "devices": devices,
        "pages": pages,
        "sessions": sessions,
        "monthly_users": monthly_users,
        "avg_session_duration_seconds": avg_seconds,
        "avg_session_duration": _format_duration(avg_seconds),
        "period_start": (today - timedelta(days=30)).isoformat(),
        "period_end": today.isoformat(),
    }


def get_site_analytics(*, force_refresh: bool = False) -> dict:
    """Return cached GA4 overview metrics for the admin dashboard."""
    if not is_analytics_configured():
        return {
            "configured": False,
            "error": (
                "Google Analytics is not fully configured. Set GA_MEASUREMENT_ID, "
                "GA4_PROPERTY_ID, and GA4_CREDENTIALS_JSON (or GA4_CREDENTIALS_FILE)."
            ),
            "visitors": {"daily": 0, "weekly": 0, "monthly": 0},
            "new_users": 0,
            "returning_users": 0,
            "countries": [],
            "devices": [],
            "pages": [],
            "sessions": 0,
            "monthly_users": 0,
            "avg_session_duration": "—",
            "avg_session_duration_seconds": 0,
            "range_label": "Last 30 days",
        }

    if not force_refresh:
        cached = cache.get(CACHE_KEY)
        if cached is not None:
            return cached

    try:
        data = _fetch_overview()
    except Exception as exc:  # noqa: BLE001 — surface any GA/API failure in the UI
        logger.exception("Failed to load Google Analytics dashboard metrics")
        data = {
            "configured": True,
            "error": str(exc),
            "visitors": {"daily": 0, "weekly": 0, "monthly": 0},
            "new_users": 0,
            "returning_users": 0,
            "countries": [],
            "devices": [],
            "pages": [],
            "sessions": 0,
            "monthly_users": 0,
            "avg_session_duration": "—",
            "avg_session_duration_seconds": 0,
            "range_label": "Last 30 days",
        }
    else:
        cache.set(CACHE_KEY, data, CACHE_TTL_SECONDS)

    return data
