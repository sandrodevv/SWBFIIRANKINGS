from django.db import transaction
from django.db.models import Count, F, Prefetch, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.characters.models import Character
from apps.rankings.models import CharacterRanking, Duelist, Player, VoteRecord
from apps.rankings.services.duelist_voting import (
    DUELIST_REGIONS,
    get_active_duelist_vote_record,
    get_all_duelist_vote_statuses,
    get_duelist_vote_status,
    record_duelist_vote,
)
from apps.rankings.services.voting import (
    ensure_voter_cookie,
    get_active_vote_record,
    get_vote_fingerprints,
    get_vote_status,
    record_vote,
)
from apps.rankings.services.pfp import (
    get_pfp_leaderboard_queryset,
    recalculate_all_pfp_scores,
    serialize_pfp_ranking,
)

from .pagination import RankingsPagination, StandardPagination
from .serializers import (
    ChampionSerializer,
    CharacterDetailSerializer,
    CharacterSerializer,
    DuelistRankingSerializer,
    PlayerProfileSerializer,
    PfpRankingSerializer,
    RankingSerializer,
    RecentVoteSerializer,
    VoteStatusSerializer,
)

DUELIST_REGION_FILTERS = {"eu", "us", "au", "overall"}
DUELIST_PERIOD_FILTERS = {"weekly", "all_time"}


class CharacterViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"

    def get_queryset(self):
        rankings_prefetch = Prefetch(
            "rankings",
            queryset=CharacterRanking.objects.select_related("player").order_by(
                "-votes", "created_at"
            ),
        )
        return Character.objects.annotate(
            total_votes_sum=Sum("rankings__votes"),
            ranked_player_count=Count("rankings"),
        ).prefetch_related(rankings_prefetch)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CharacterDetailSerializer
        return CharacterSerializer

    @action(detail=True, methods=["get"], url_path="vote-status")
    def vote_status(self, request, slug=None):
        character = self.get_object()
        ip_hash, voter_hash = get_vote_fingerprints(request)
        status_data = get_vote_status(character.id, ip_hash, voter_hash)
        serializer = VoteStatusSerializer(status_data)
        response = Response(serializer.data)
        ensure_voter_cookie(request, response)
        return response

    @action(detail=True, methods=["get"], pagination_class=RankingsPagination)
    def rankings(self, request, slug=None):
        character = self.get_object()
        queryset = character.rankings.select_related("player").order_by("-votes", "created_at")

        paginator = RankingsPagination()
        page = paginator.paginate_queryset(queryset, request)
        start_rank = (paginator.page.number - 1) * paginator.page_size + 1 if page else 1

        for index, ranking in enumerate(page or []):
            ranking.computed_rank = start_rank + index

        serializer = RankingSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class ChampionListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        champions = []
        characters = Character.objects.all().order_by("name")

        for character in characters:
            top = (
                character.rankings.select_related("player")
                .order_by("-votes", "created_at")
                .first()
            )
            if not top:
                continue

            image_url = character.get_image_url(request)

            champions.append(
                {
                    "character_id": character.id,
                    "character_name": character.name,
                    "character_slug": character.slug,
                    "character_side": character.side,
                    "image_url": image_url,
                    "player_nickname": top.player.nickname,
                    "player_username": top.player.username or None,
                    "player_slug": top.player.slug,
                    "player_name_burning": top.player.name_burning,
                    "player_name_smoke": top.player.name_smoke,
                    "player_name_glitch": top.player.name_glitch,
                    "player_all_time_votes": top.player.all_time_votes,
                    "votes": top.votes,
                }
            )

        serializer = ChampionSerializer(champions, many=True)
        return Response(serializer.data)


class VoteAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        ranking = get_object_or_404(
            CharacterRanking.objects.select_related("character", "player"),
            pk=pk,
        )
        ip_hash, voter_hash = get_vote_fingerprints(request)
        character = ranking.character

        existing = get_active_vote_record(character.id, ip_hash, voter_hash)
        if existing:
            status_data = get_vote_status(character.id, ip_hash, voter_hash)
            response = Response(
                {
                    "detail": status_data["message"],
                    **status_data,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
            ensure_voter_cookie(request, response)
            return response

        with transaction.atomic():
            CharacterRanking.objects.filter(pk=pk).update(
                votes=F("votes") + 1,
                all_time_votes=F("all_time_votes") + 1,
            )
            Player.objects.filter(pk=ranking.player_id).update(
                all_time_votes=F("all_time_votes") + 1,
            )
            record_vote(character, ranking, ip_hash, voter_hash)
            ranking.refresh_from_db()
            ranking.player.refresh_from_db()
            recalculate_all_pfp_scores()

        ordered = list(
            character.rankings.order_by("-votes", "created_at").values_list("id", flat=True)
        )
        ranking.computed_rank = ordered.index(ranking.id) + 1

        serializer = RankingSerializer(ranking, context={"request": request})
        response = Response(serializer.data, status=status.HTTP_200_OK)
        ensure_voter_cookie(request, response)
        return response


def _build_character_stat(ranking):
    character = ranking.character
    ordered_ids = list(
        character.rankings.order_by("-votes", "created_at").values_list("id", flat=True)
    )
    try:
        rank = ordered_ids.index(ranking.id) + 1
    except ValueError:
        rank = None

    return {
        "character_name": character.name,
        "character_slug": character.slug,
        "side": character.side,
        "rank": rank,
        "weekly_votes": ranking.votes,
        "all_time_votes": ranking.all_time_votes,
    }


def _duelist_rank(duelist, queryset):
    ordered_ids = list(queryset.order_by("-votes", "created_at").values_list("id", flat=True))
    try:
        return ordered_ids.index(duelist.id) + 1
    except ValueError:
        return None


def _build_duelist_stat(duelist):
    character = duelist.character
    return {
        "region": duelist.region,
        "region_label": duelist.get_region_display(),
        "character_name": character.name,
        "character_slug": character.slug,
        "character_side": character.side,
        "region_rank": _duelist_rank(
            duelist, Duelist.objects.filter(region=duelist.region)
        ),
        "overall_rank": _duelist_rank(duelist, Duelist.objects.all()),
        "weekly_votes": duelist.votes,
        "all_time_votes": duelist.all_time_votes,
    }


class PlayerDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        player = get_object_or_404(
            Player.objects.prefetch_related("rankings__character"),
            slug=slug,
        )
        rankings = list(
            player.rankings.select_related("character").order_by("-votes", "character__name")
        )
        character_stats = [_build_character_stat(ranking) for ranking in rankings]
        ranking_weekly_votes = sum(stat["weekly_votes"] for stat in character_stats)
        ranking_all_time_votes = sum(stat["all_time_votes"] for stat in character_stats)

        hero_assignment = next((stat for stat in character_stats if stat["side"] == "hero"), None)
        villain_assignment = next(
            (stat for stat in character_stats if stat["side"] == "villain"), None
        )

        duelist_stat = None
        duelist_weekly_votes = 0
        duelist_all_time_votes = 0
        try:
            duelist = player.duelist
        except Duelist.DoesNotExist:
            duelist = None
        if duelist is not None:
            duelist_stat = _build_duelist_stat(duelist)
            duelist_weekly_votes = duelist.votes
            duelist_all_time_votes = duelist.all_time_votes

        payload = {
            "nickname": player.nickname,
            "username": player.username or None,
            "slug": player.slug,
            "discord_url": player.discord_url or "",
            "steam_url": player.steam_url or "",
            "twitch_url": player.twitch_url or "",
            "name_burning": player.name_burning,
            "name_smoke": player.name_smoke,
            "name_glitch": player.name_glitch,
            "weekly_votes": ranking_weekly_votes + duelist_weekly_votes,
            "all_time_votes": ranking_all_time_votes + duelist_all_time_votes,
            "ranking_weekly_votes": ranking_weekly_votes,
            "ranking_all_time_votes": ranking_all_time_votes,
            "duelist_weekly_votes": duelist_weekly_votes,
            "duelist_all_time_votes": duelist_all_time_votes,
            "hero_gold_medals": player.hero_gold_medals,
            "villain_gold_medals": player.villain_gold_medals,
            "hero_assignment": hero_assignment,
            "villain_assignment": villain_assignment,
            "duelist": duelist_stat,
        }
        serializer = PlayerProfileSerializer(payload)
        return Response(serializer.data)


class RecentVotesAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        records = VoteRecord.objects.select_related(
            "character",
            "ranking__player",
        ).order_by("-voted_at")[:20]

        votes = [
            {
                "player_nickname": record.ranking.player.nickname,
                "player_slug": record.ranking.player.slug,
                "player_username": record.ranking.player.username or None,
                "player_name_burning": record.ranking.player.name_burning,
                "player_name_smoke": record.ranking.player.name_smoke,
                "player_name_glitch": record.ranking.player.name_glitch,
                "character_name": record.character.name,
                "character_slug": record.character.slug,
                "character_side": record.character.side,
                "voted_at": record.voted_at,
            }
            for record in records
        ]
        serializer = RecentVoteSerializer(votes, many=True)
        return Response(serializer.data)


class PfpLeaderboardAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = get_pfp_leaderboard_queryset()

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)

        results = [serialize_pfp_ranking(ranking) for ranking in page or []]
        serializer = PfpRankingSerializer(results, many=True)
        return paginator.get_paginated_response(serializer.data)


def _duelist_order_fields(period):
    if period == "all_time":
        return ("-all_time_votes", "created_at")
    return ("-votes", "created_at")


def _serialize_duelist(duelist, rank):
    player = duelist.player
    return {
        "id": duelist.id,
        "rank": rank,
        "nickname": player.nickname,
        "username": player.username or None,
        "slug": player.slug,
        "name_burning": player.name_burning,
        "name_smoke": player.name_smoke,
        "name_glitch": player.name_glitch,
        "region": duelist.region,
        "region_label": duelist.get_region_display(),
        "votes": duelist.votes,
        "all_time_votes": duelist.all_time_votes,
        "character_name": duelist.character.name,
        "character_slug": duelist.character.slug,
        "character_side": duelist.character.side,
    }


class DuelistLeaderboardAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        region = (request.query_params.get("region") or "overall").lower()
        period = (request.query_params.get("period") or "weekly").lower()

        if region not in DUELIST_REGION_FILTERS:
            return Response(
                {"detail": "Invalid region. Use eu, us, au, or overall."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if period not in DUELIST_PERIOD_FILTERS:
            return Response(
                {"detail": "Invalid period. Use weekly or all_time."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = Duelist.objects.select_related("character", "player")
        if region != "overall":
            queryset = queryset.filter(region=region)
        queryset = queryset.order_by(*_duelist_order_fields(period))

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        start_rank = (paginator.page.number - 1) * paginator.page_size + 1 if page else 1

        results = [
            _serialize_duelist(duelist, start_rank + index)
            for index, duelist in enumerate(page or [])
        ]
        serializer = DuelistRankingSerializer(results, many=True)
        return paginator.get_paginated_response(serializer.data)


class DuelistVoteStatusAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ip_hash, voter_hash = get_vote_fingerprints(request)
        region = (request.query_params.get("region") or "").lower()

        if region in DUELIST_REGIONS:
            status_data = get_duelist_vote_status(ip_hash, voter_hash, region)
            serializer = VoteStatusSerializer(status_data)
            response = Response(serializer.data)
        elif region in ("", "overall"):
            response = Response(get_all_duelist_vote_statuses(ip_hash, voter_hash))
        else:
            return Response(
                {"detail": "Invalid region. Use eu, us, au, or overall."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ensure_voter_cookie(request, response)
        return response


class DuelistVoteAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        duelist = get_object_or_404(
            Duelist.objects.select_related("character", "player"),
            pk=pk,
        )
        ip_hash, voter_hash = get_vote_fingerprints(request)
        region = duelist.region

        existing = get_active_duelist_vote_record(ip_hash, voter_hash, region)
        if existing:
            status_data = get_duelist_vote_status(ip_hash, voter_hash, region)
            response = Response(
                {
                    "detail": status_data["message"],
                    **status_data,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
            ensure_voter_cookie(request, response)
            return response

        with transaction.atomic():
            Duelist.objects.filter(pk=pk).update(
                votes=F("votes") + 1,
                all_time_votes=F("all_time_votes") + 1,
            )
            record_duelist_vote(duelist, ip_hash, voter_hash)
            duelist.refresh_from_db()

        ordered_ids = list(
            Duelist.objects.order_by("-votes", "created_at").values_list("id", flat=True)
        )
        rank = ordered_ids.index(duelist.id) + 1
        serializer = DuelistRankingSerializer(_serialize_duelist(duelist, rank))
        response = Response(serializer.data, status=status.HTTP_200_OK)
        ensure_voter_cookie(request, response)
        return response
