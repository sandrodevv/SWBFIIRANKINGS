import hashlib
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.signing import BadSignature, Signer
from django.db.models import Q
from django.utils import timezone

from apps.rankings.models import VoteRecord
from apps.rankings.services.weekly_reset import (
    ensure_current_period,
    get_period_duration,
    get_period_end,
)

VOTER_COOKIE_NAME = "bf2_voter"
VOTER_COOKIE_MAX_AGE = 60 * 60 * 24 * 365
_signer = Signer(salt="bf2-voter")


def get_vote_cooldown():
    return get_period_duration()


def hash_fingerprint(value: str) -> str:
    payload = f"{settings.SECRET_KEY}:{value}"
    return hashlib.sha256(payload.encode()).hexdigest()


def get_client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_or_create_voter_id(request, response=None):
    raw_cookie = request.COOKIES.get(VOTER_COOKIE_NAME)
    if raw_cookie:
        try:
            return _signer.unsign(raw_cookie), False
        except BadSignature:
            pass

    voter_id = str(uuid.uuid4())
    if response is not None:
        response.set_cookie(
            VOTER_COOKIE_NAME,
            _signer.sign(voter_id),
            max_age=VOTER_COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
            secure=not settings.DEBUG,
        )
    return voter_id, True


def get_voter_id_from_request(request):
    raw_cookie = request.COOKIES.get(VOTER_COOKIE_NAME)
    if raw_cookie:
        try:
            return _signer.unsign(raw_cookie)
        except BadSignature:
            pass
    return None


def ensure_voter_cookie(request, response):
    if VOTER_COOKIE_NAME not in request.COOKIES:
        get_or_create_voter_id(request, response=response)


def get_vote_fingerprints(request):
    ip = get_client_ip(request)
    ip_hash = hash_fingerprint(ip)
    voter_id = get_voter_id_from_request(request)
    if voter_id:
        voter_hash = hash_fingerprint(voter_id)
    else:
        voter_hash = hash_fingerprint(f"ip-only:{ip}")
    return ip_hash, voter_hash


def get_active_vote_record(character_id, ip_hash, voter_hash):
    period = ensure_current_period()
    return (
        VoteRecord.objects.filter(
            character_id=character_id,
            voted_at__gte=period.started_at,
        )
        .filter(Q(ip_hash=ip_hash) | Q(voter_hash=voter_hash))
        .select_related("ranking__player")
        .order_by("-voted_at")
        .first()
    )


def get_vote_status(character_id, ip_hash, voter_hash):
    period = ensure_current_period()
    record = get_active_vote_record(character_id, ip_hash, voter_hash)
    if not record:
        return {
            "can_vote": True,
            "voted_at": None,
            "next_vote_at": None,
            "cooldown_days": get_vote_cooldown().days,
            "message": None,
            "last_voted_player": None,
            "last_voted_username": None,
            "last_voted_name_burning": None,
            "last_voted_name_smoke": None,
            "last_voted_name_glitch": None,
            "period_ends_at": get_period_end(period).isoformat(),
        }

    next_vote_at = get_period_end(period)
    player = record.ranking.player
    return {
        "can_vote": False,
        "voted_at": record.voted_at.isoformat(),
        "next_vote_at": next_vote_at.isoformat(),
        "cooldown_days": get_vote_cooldown().days,
        "message": (
            f"You can vote again on this character when the weekly rankings reset "
            f"on {next_vote_at.strftime('%b %d, %Y %H:%M UTC')}."
        ),
        "last_voted_player": player.nickname,
        "last_voted_username": player.username or None,
        "last_voted_name_burning": player.name_burning,
        "last_voted_name_smoke": player.name_smoke,
        "last_voted_name_glitch": player.name_glitch,
        "period_ends_at": next_vote_at.isoformat(),
    }


def record_vote(character, ranking, ip_hash, voter_hash):
    return VoteRecord.objects.create(
        character=character,
        ranking=ranking,
        ip_hash=ip_hash,
        voter_hash=voter_hash,
    )
