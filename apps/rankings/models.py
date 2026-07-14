from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.characters.models import Character

from .utils import generate_unique_player_slug
from .validators import validate_player_side_assignment


class Player(models.Model):
    nickname = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    discord_url = models.URLField(
        max_length=200,
        blank=True,
        help_text="Public Discord profile or invite link for this player.",
    )
    steam_url = models.URLField(
        max_length=200,
        blank=True,
        help_text="Public Steam profile link for this player.",
    )
    twitch_url = models.URLField(
        max_length=200,
        blank=True,
        help_text="Public Twitch channel link for this player.",
    )
    all_time_votes = models.PositiveIntegerField(
        default=0,
        help_text="Total votes received across all characters and weekly periods.",
    )
    name_burning = models.BooleanField(
        default=False,
        help_text="Show the burning nickname animation on this player everywhere.",
    )
    name_smoke = models.BooleanField(
        default=False,
        help_text="Show the smoke nickname animation on this player everywhere.",
    )
    name_glitch = models.BooleanField(
        default=False,
        help_text="Show the glitch nickname animation on this player everywhere.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nickname"]

    def __str__(self):
        return self.nickname

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_player_slug(self.nickname, exclude_pk=self.pk)
        super().save(*args, **kwargs)


class Duelist(models.Model):
    REGION_EU = "eu"
    REGION_US = "us"
    REGION_AU = "au"
    REGION_CHOICES = [
        (REGION_EU, "EU"),
        (REGION_US, "US"),
        (REGION_AU, "AU"),
    ]

    player = models.OneToOneField(
        Player,
        related_name="duelist",
        on_delete=models.CASCADE,
    )
    region = models.CharField(max_length=2, choices=REGION_CHOICES)
    character = models.ForeignKey(
        Character,
        related_name="duelists",
        on_delete=models.PROTECT,
        help_text="The single Saber Hero this duelist represents.",
        limit_choices_to={"combat_type": Character.COMBAT_SABER},
    )
    votes = models.PositiveIntegerField(
        default=0,
        help_text="Current weekly vote count (resets each voting period).",
    )
    last_week_votes = models.PositiveIntegerField(
        default=0,
        help_text="Vote count from the previous weekly period (overwritten each reset).",
    )
    all_time_votes = models.PositiveIntegerField(
        default=0,
        help_text="Total votes received across all weekly periods.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-votes", "created_at"]

    def __str__(self):
        return (
            f"{self.player.nickname} ({self.get_region_display()}) — {self.character.name}"
        )

    def clean(self):
        super().clean()
        if self.character_id and self.character.combat_type != Character.COMBAT_SABER:
            raise ValidationError(
                {"character": "Duelists can only represent Saber heroes (no blasters or balls)."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CharacterRanking(models.Model):
    character = models.ForeignKey(
        Character,
        related_name="rankings",
        on_delete=models.CASCADE,
    )
    player = models.ForeignKey(
        Player,
        related_name="rankings",
        on_delete=models.CASCADE,
    )
    votes = models.PositiveIntegerField(
        default=0,
        help_text="Current weekly vote count (resets each voting period).",
    )
    last_week_votes = models.PositiveIntegerField(
        default=0,
        help_text="Vote count from the previous weekly period (overwritten each reset).",
    )
    all_time_votes = models.PositiveIntegerField(
        default=0,
        help_text="Total votes received across all weekly periods.",
    )
    pfp_score = models.FloatField(default=0)
    pfp_percentile_score = models.FloatField(default=0)
    pfp_vote_score = models.FloatField(default=0)
    pfp_competition_score = models.FloatField(default=0)
    pfp_champion_bonus = models.FloatField(default=0)
    pfp_character_rank = models.PositiveIntegerField(default=0)
    pfp_global_rank = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-votes", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["character", "player"],
                name="unique_character_player",
            )
        ]

    def __str__(self):
        return f"{self.player.nickname} — {self.character.name} ({self.votes} weekly votes)"

    def clean(self):
        super().clean()
        if self.player_id and self.character_id:
            validate_player_side_assignment(self.player, self.character, self.pk)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class WeeklyVotePeriod(models.Model):
    started_at = models.DateTimeField(
        help_text="When the current weekly voting period began.",
    )

    class Meta:
        verbose_name = "Weekly vote period"
        verbose_name_plural = "Weekly vote period"

    def __str__(self):
        return f"Weekly period started {self.started_at}"

    @classmethod
    def get_singleton(cls):
        from apps.rankings.services.weekly_reset import get_scheduled_period_start

        period, _ = cls.objects.get_or_create(
            pk=1,
            defaults={"started_at": get_scheduled_period_start()},
        )
        return period


class VoteRecord(models.Model):
    character = models.ForeignKey(
        Character,
        related_name="vote_records",
        on_delete=models.CASCADE,
    )
    ranking = models.ForeignKey(
        CharacterRanking,
        related_name="vote_records",
        on_delete=models.CASCADE,
    )
    ip_hash = models.CharField(max_length=64, db_index=True)
    voter_hash = models.CharField(max_length=64, db_index=True)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-voted_at"]
        indexes = [
            models.Index(fields=["character", "ip_hash", "voted_at"]),
            models.Index(fields=["character", "voter_hash", "voted_at"]),
        ]

    def __str__(self):
        return f"Vote on {self.character.name} at {self.voted_at}"


class DuelistVoteRecord(models.Model):
    duelist = models.ForeignKey(
        Duelist,
        related_name="vote_records",
        on_delete=models.CASCADE,
    )
    ip_hash = models.CharField(max_length=64, db_index=True)
    voter_hash = models.CharField(max_length=64, db_index=True)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-voted_at"]
        indexes = [
            models.Index(fields=["ip_hash", "voted_at"]),
            models.Index(fields=["voter_hash", "voted_at"]),
        ]

    def __str__(self):
        return f"Duelist vote for {self.duelist.player.nickname} at {self.voted_at}"


class DiscordNotificationLog(models.Model):
    """Idempotency log for automated Discord notifications."""

    TYPE_PFP_WEEKLY_ENDING = "pfp_weekly_ending"
    TYPE_CHOICES = [
        (TYPE_PFP_WEEKLY_ENDING, "PFP weekly ending rankings"),
    ]

    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
    ]

    notification_type = models.CharField(max_length=64, choices=TYPE_CHOICES)
    period_started_at = models.DateTimeField(
        help_text="WeeklyVotePeriod.started_at this notification belongs to.",
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    entry_count = models.PositiveIntegerField(default=0)
    detail = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["notification_type", "period_started_at"],
                name="unique_discord_notification_per_period",
            )
        ]
        ordering = ["-created_at"]
        verbose_name = "Discord notification log"
        verbose_name_plural = "Discord notification logs"

    def __str__(self):
        return (
            f"{self.get_notification_type_display()} "
            f"({self.period_started_at.isoformat()}) — {self.status}"
        )
