from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET


def _favicon_path() -> Path:
    candidates = [
        Path(settings.STATIC_ROOT) / "images" / "favicon.png",
        Path(settings.BASE_DIR) / "frontend" / "static" / "images" / "favicon.png",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise Http404("Favicon not found")


@require_GET
@cache_control(max_age=60 * 60 * 24 * 7, public=True, immutable=True)
def favicon_ico(request):
    """Stable root favicon URL for Google Search and browser defaults."""
    path = _favicon_path()
    return FileResponse(path.open("rb"), content_type="image/png")


class ApiNoIndexMiddleware(MiddlewareMixin):
    """Keep API JSON out of Google Search while allowing crawlers to fetch it."""

    def process_response(self, request, response):
        if request.path.startswith("/api/"):
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
