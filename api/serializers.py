from django.db.models import Count, Sum
from rest_framework import serializers

from apps.characters.models import Character
from apps.rankings.models import CharacterRanking, Player


class TopPlayerSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    username = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    player_slug = serializers.CharField()
    votes = serializers.IntegerField()
    player_all_time_votes = serializers.IntegerField()
    name_burning = serializers.BooleanField()
    name_smoke = serializers.BooleanField()
    name_glitch = serializers.BooleanField()


class PlayerCharacterStatSerializer(serializers.Serializer):
    character_name = serializers.CharField()
    character_slug = serializers.CharField()
    side = serializers.CharField()
    rank = serializers.IntegerField()
    weekly_votes = serializers.IntegerField()
    all_time_votes = serializers.IntegerField()


class PlayerDuelistStatSerializer(serializers.Serializer):
    region = serializers.CharField()
    region_label = serializers.CharField()
    character_name = serializers.CharField()
    character_slug = serializers.CharField()
    character_side = serializers.CharField()
    region_rank = serializers.IntegerField(allow_null=True)
    overall_rank = serializers.IntegerField(allow_null=True)
    weekly_votes = serializers.IntegerField()
    all_time_votes = serializers.IntegerField()


class PlayerProfileSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    username = serializers.CharField(allow_null=True)
    slug = serializers.CharField()
    discord_url = serializers.URLField(allow_blank=True, required=False)
    steam_url = serializers.URLField(allow_blank=True, required=False)
    twitch_url = serializers.URLField(allow_blank=True, required=False)
    name_burning = serializers.BooleanField()
    name_smoke = serializers.BooleanField()
    name_glitch = serializers.BooleanField()
    all_time_votes = serializers.IntegerField()
    weekly_votes = serializers.IntegerField()
    ranking_weekly_votes = serializers.IntegerField()
    ranking_all_time_votes = serializers.IntegerField()
    duelist_weekly_votes = serializers.IntegerField()
    duelist_all_time_votes = serializers.IntegerField()
    hero_assignment = PlayerCharacterStatSerializer(allow_null=True)
    villain_assignment = PlayerCharacterStatSerializer(allow_null=True)
    duelist = PlayerDuelistStatSerializer(allow_null=True)


class CharacterSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    top_player = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()
    ranked_player_count = serializers.SerializerMethodField()

    class Meta:
        model = Character
        fields = [
            "id",
            "name",
            "slug",
            "side",
            "image_url",
            "top_player",
            "total_votes",
            "ranked_player_count",
        ]

    def get_image_url(self, obj):
        return obj.get_image_url(self.context.get("request"))

    def get_top_player(self, obj):
        rankings = list(obj.rankings.all())
        if not rankings:
            return None
        top = rankings[0]
        return {
            "nickname": top.player.nickname,
            "username": top.player.username or None,
            "player_slug": top.player.slug,
            "votes": top.votes,
            "player_all_time_votes": top.player.all_time_votes,
            "name_burning": top.player.name_burning,
            "name_smoke": top.player.name_smoke,
            "name_glitch": top.player.name_glitch,
        }

    def get_total_votes(self, obj):
        if hasattr(obj, "total_votes_sum"):
            return obj.total_votes_sum or 0
        return obj.rankings.aggregate(total=Sum("votes"))["total"] or 0

    def get_ranked_player_count(self, obj):
        if hasattr(obj, "ranked_player_count"):
            return obj.ranked_player_count
        return obj.rankings.count()


class CharacterDetailSerializer(CharacterSerializer):
    class Meta(CharacterSerializer.Meta):
        fields = CharacterSerializer.Meta.fields + ["description"]


class RankingSerializer(serializers.ModelSerializer):
    rank = serializers.SerializerMethodField()
    nickname = serializers.CharField(source="player.nickname", read_only=True)
    username = serializers.SerializerMethodField()
    character_slug = serializers.CharField(source="character.slug", read_only=True)
    character_side = serializers.CharField(source="character.side", read_only=True)
    player_all_time_votes = serializers.IntegerField(source="player.all_time_votes", read_only=True)
    player_slug = serializers.CharField(source="player.slug", read_only=True)
    name_burning = serializers.BooleanField(source="player.name_burning", read_only=True)
    name_smoke = serializers.BooleanField(source="player.name_smoke", read_only=True)
    name_glitch = serializers.BooleanField(source="player.name_glitch", read_only=True)

    class Meta:
        model = CharacterRanking
        fields = [
            "id",
            "rank",
            "nickname",
            "username",
            "player_slug",
            "name_burning",
            "name_smoke",
            "name_glitch",
            "votes",
            "all_time_votes",
            "player_all_time_votes",
            "character_slug",
            "character_side",
        ]

    def get_username(self, obj):
        return obj.player.username or None

    def get_rank(self, obj):
        if hasattr(obj, "computed_rank"):
            return obj.computed_rank
        rankings = list(
            obj.character.rankings.order_by("-votes", "created_at").values_list("id", flat=True)
        )
        try:
            return rankings.index(obj.id) + 1
        except ValueError:
            return None


class VoteStatusSerializer(serializers.Serializer):
    can_vote = serializers.BooleanField()
    voted_at = serializers.CharField(allow_null=True)
    next_vote_at = serializers.CharField(allow_null=True)
    cooldown_days = serializers.IntegerField()
    message = serializers.CharField(allow_null=True)
    last_voted_player = serializers.CharField(allow_null=True)
    last_voted_username = serializers.CharField(allow_null=True)
    last_voted_name_burning = serializers.BooleanField(required=False, allow_null=True)
    last_voted_name_smoke = serializers.BooleanField(required=False, allow_null=True)
    last_voted_name_glitch = serializers.BooleanField(required=False, allow_null=True)
    period_ends_at = serializers.CharField(allow_null=True)


class ChampionSerializer(serializers.Serializer):
    character_id = serializers.IntegerField()
    character_name = serializers.CharField()
    character_slug = serializers.CharField()
    character_side = serializers.CharField()
    image_url = serializers.CharField()
    player_nickname = serializers.CharField()
    player_username = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    player_slug = serializers.CharField()
    player_name_burning = serializers.BooleanField()
    player_name_smoke = serializers.BooleanField()
    player_name_glitch = serializers.BooleanField()
    player_all_time_votes = serializers.IntegerField()
    votes = serializers.IntegerField()


class RecentVoteSerializer(serializers.Serializer):
    player_nickname = serializers.CharField()
    player_slug = serializers.CharField()
    player_username = serializers.CharField(allow_null=True)
    player_name_burning = serializers.BooleanField()
    player_name_smoke = serializers.BooleanField()
    player_name_glitch = serializers.BooleanField()
    character_name = serializers.CharField()
    character_slug = serializers.CharField()
    character_side = serializers.CharField()
    voted_at = serializers.DateTimeField()


class PfpRankingSerializer(serializers.Serializer):
    global_rank = serializers.IntegerField()
    pfp_score = serializers.FloatField()
    percentile_score = serializers.FloatField()
    vote_score = serializers.FloatField()
    competition_score = serializers.FloatField()
    champion_bonus = serializers.FloatField()
    character_rank = serializers.IntegerField()
    all_time_votes = serializers.IntegerField()
    player_nickname = serializers.CharField()
    player_username = serializers.CharField(allow_null=True)
    player_slug = serializers.CharField()
    player_name_burning = serializers.BooleanField()
    player_name_smoke = serializers.BooleanField()
    player_name_glitch = serializers.BooleanField()
    character_name = serializers.CharField()
    character_slug = serializers.CharField()
    character_side = serializers.CharField()


class DuelistRankingSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    rank = serializers.IntegerField()
    nickname = serializers.CharField()
    username = serializers.CharField(allow_null=True)
    slug = serializers.CharField()
    name_burning = serializers.BooleanField()
    name_smoke = serializers.BooleanField()
    name_glitch = serializers.BooleanField()
    region = serializers.CharField()
    region_label = serializers.CharField()
    votes = serializers.IntegerField()
    all_time_votes = serializers.IntegerField()
    character_name = serializers.CharField()
    character_slug = serializers.CharField()
    character_side = serializers.CharField()
