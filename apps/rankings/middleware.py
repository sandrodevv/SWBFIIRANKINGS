from django.utils.deprecation import MiddlewareMixin

from apps.rankings.services.voting import VOTER_COOKIE_NAME, get_or_create_voter_id
from apps.rankings.services.weekly_reset import ensure_current_period


class VoterCookieMiddleware(MiddlewareMixin):
    """Assign a signed HttpOnly cookie to identify the browser between visits."""

    def process_response(self, request, response):
        if VOTER_COOKIE_NAME not in request.COOKIES:
            get_or_create_voter_id(request, response=response)
        return response


class WeeklyResetMiddleware(MiddlewareMixin):
    """Reset weekly vote counts when a new voting period begins."""

    def process_request(self, request):
        if request.path.startswith("/api/"):
            ensure_current_period()
