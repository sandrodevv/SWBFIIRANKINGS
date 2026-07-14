from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ChampionListAPIView,
    CharacterViewSet,
    DuelistLeaderboardAPIView,
    DuelistVoteAPIView,
    DuelistVoteStatusAPIView,
    PfpLeaderboardAPIView,
    PlayerDetailAPIView,
    RecentVotesAPIView,
    VoteAPIView,
)

router = DefaultRouter()
router.register("characters", CharacterViewSet, basename="character")

urlpatterns = [
    path("", include(router.urls)),
    path("champions/", ChampionListAPIView.as_view(), name="champions"),
    path("pfp/", PfpLeaderboardAPIView.as_view(), name="pfp-leaderboard"),
    path("duelists/", DuelistLeaderboardAPIView.as_view(), name="duelist-leaderboard"),
    path(
        "duelists/vote-status/",
        DuelistVoteStatusAPIView.as_view(),
        name="duelist-vote-status",
    ),
    path("duelists/<int:pk>/vote/", DuelistVoteAPIView.as_view(), name="duelist-vote"),
    path("recent-votes/", RecentVotesAPIView.as_view(), name="recent-votes"),
    path("players/<slug:slug>/", PlayerDetailAPIView.as_view(), name="player-detail"),
    path("rankings/<int:pk>/vote/", VoteAPIView.as_view(), name="ranking-vote"),
]
