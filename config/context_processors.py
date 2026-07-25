from django.conf import settings


def analytics(request):
    """Expose Google Analytics measurement ID to public templates."""
    return {
        "GA_MEASUREMENT_ID": getattr(settings, "GA_MEASUREMENT_ID", "") or "",
    }
