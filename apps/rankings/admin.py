from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from apps.characters.models import Character
from apps.rankings.models import (
    CharacterRanking,
    DiscordNotificationLog,
    Duelist,
    DuelistVoteRecord,
    Player,
    VoteRecord,
    WeeklyVotePeriod,
)
from apps.rankings.validators import (
    player_side_assignment_conflict,
    validate_player_side_assignment,
)


class CharacterRankingForm(forms.ModelForm):
    class Meta:
        model = CharacterRanking
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        player = cleaned_data.get("player")
        if player is None and self.instance.player_id:
            player = self.instance.player
        character = cleaned_data.get("character")
        if player is None and self.instance.character_id:
            character = self.instance.character
        if player and player.pk and character:
            validate_player_side_assignment(player, character, self.instance.pk)
        return cleaned_data

    def save(self, commit=True):
        """Keep all_time_votes in sync when weekly votes are edited in admin."""
        instance = super().save(commit=False)
        if self.instance.pk and "votes" in self.changed_data:
            previous = self.initial.get("votes")
            if previous is None:
                previous = 0
            delta = int(instance.votes) - int(previous)
            instance.all_time_votes = max(0, int(instance.all_time_votes) + delta)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class DuelistForm(forms.ModelForm):
    class Meta:
        model = Duelist
        fields = "__all__"

    def save(self, commit=True):
        """Keep all_time_votes in sync when weekly votes are edited in admin."""
        instance = super().save(commit=False)
        if self.instance.pk and "votes" in self.changed_data:
            previous = self.initial.get("votes")
            if previous is None:
                previous = 0
            delta = int(instance.votes) - int(previous)
            instance.all_time_votes = max(0, int(instance.all_time_votes) + delta)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class CharacterRankingInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        player = self.instance
        side_counts = {Character.SIDE_HERO: 0, Character.SIDE_VILLAIN: 0}

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue
            character = form.cleaned_data.get("character")
            if not character:
                continue

            side_counts[character.side] += 1
            if side_counts[character.side] > 1:
                side_label = "Hero" if character.side == Character.SIDE_HERO else "Villain"
                raise ValidationError(
                    f"Each player can only have one {side_label} assignment."
                )

        if not player.pk:
            return

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue
            character = form.cleaned_data.get("character")
            if not character:
                continue

            conflict = player_side_assignment_conflict(player, character, form.instance.pk)
            if conflict:
                side_label = "Hero" if character.side == Character.SIDE_HERO else "Villain"
                raise ValidationError(
                    f"{player.nickname} is already assigned to {conflict.character.name} "
                    f"({side_label}). Each player can only be ranked on one Hero and one Villain."
                )


class CharacterRankingInline(admin.TabularInline):
    model = CharacterRanking
    form = CharacterRankingForm
    formset = CharacterRankingInlineFormSet
    extra = 1
    max_num = 2
    fields = ("character", "votes", "last_week_votes", "all_time_votes")
    autocomplete_fields = ("character",)
    verbose_name = "Character assignment"
    verbose_name_plural = "Character assignments (one Hero and one Villain)"


class DuelistInline(admin.StackedInline):
    model = Duelist
    form = DuelistForm
    extra = 0
    max_num = 1
    fields = ("region", "character", "votes", "last_week_votes", "all_time_votes")
    autocomplete_fields = ("character",)
    verbose_name = "Best Duelist profile"
    verbose_name_plural = "Best Duelist profile (optional)"


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "nickname",
        "slug",
        "username",
        "all_time_votes",
        "name_burning",
        "name_smoke",
        "name_glitch",
        "assignment_summary",
        "duelist_summary",
        "created_at",
    )
    list_filter = ("name_burning", "name_smoke", "name_glitch")
    search_fields = ("nickname", "username", "slug")
    prepopulated_fields = {"slug": ("nickname",)}
    readonly_fields = ("all_time_votes", "created_at")
    fields = (
        "nickname",
        "slug",
        "username",
        "discord_url",
        "steam_url",
        "twitch_url",
        "all_time_votes",
        "name_burning",
        "name_smoke",
        "name_glitch",
        "created_at",
    )
    inlines = (CharacterRankingInline, DuelistInline)

    @admin.display(description="Assignments")
    def assignment_summary(self, obj):
        if not obj.pk:
            return "—"
        rankings = obj.rankings.select_related("character").order_by(
            "character__side", "character__name"
        )
        if not rankings:
            return "—"
        return ", ".join(f"{r.character.name} ({r.character.side})" for r in rankings)

    @admin.display(description="Duelist")
    def duelist_summary(self, obj):
        if not obj.pk or not hasattr(obj, "duelist"):
            return "—"
        duelist = obj.duelist
        return f"{duelist.get_region_display()} — {duelist.character.name}"


@admin.register(CharacterRanking)
class CharacterRankingAdmin(admin.ModelAdmin):
    form = CharacterRankingForm
    list_display = ("player", "character", "votes", "last_week_votes", "all_time_votes", "created_at")
    list_filter = ("character__side", "character")
    search_fields = ("player__nickname", "character__name")
    autocomplete_fields = ("player", "character")
    ordering = ("character", "-votes", "created_at")


@admin.register(Duelist)
class DuelistAdmin(admin.ModelAdmin):
    form = DuelistForm
    list_display = (
        "player",
        "region",
        "character",
        "votes",
        "last_week_votes",
        "all_time_votes",
        "created_at",
    )
    list_filter = ("region", "character__side", "character")
    search_fields = ("player__nickname", "player__username", "player__slug", "character__name")
    autocomplete_fields = ("player", "character")
    readonly_fields = ("created_at",)
    fields = (
        "player",
        "region",
        "character",
        "votes",
        "last_week_votes",
        "all_time_votes",
        "created_at",
    )
    ordering = ("region", "-votes", "player__nickname")


@admin.register(VoteRecord)
class VoteRecordAdmin(admin.ModelAdmin):
    list_display = ("character", "ranking", "voted_at", "ip_hash", "voter_hash")
    list_filter = ("character", "voted_at")
    search_fields = ("ranking__player__nickname", "character__name")
    readonly_fields = ("character", "ranking", "ip_hash", "voter_hash", "voted_at")
    ordering = ("-voted_at",)


@admin.register(DuelistVoteRecord)
class DuelistVoteRecordAdmin(admin.ModelAdmin):
    list_display = ("duelist", "voted_at", "ip_hash", "voter_hash")
    list_filter = ("voted_at", "duelist__region")
    search_fields = ("duelist__player__nickname",)
    readonly_fields = ("duelist", "ip_hash", "voter_hash", "voted_at")
    ordering = ("-voted_at",)


@admin.register(WeeklyVotePeriod)
class WeeklyVotePeriodAdmin(admin.ModelAdmin):
    list_display = ("started_at",)
    readonly_fields = ("started_at",)

    def has_add_permission(self, request):
        return not WeeklyVotePeriod.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DiscordNotificationLog)
class DiscordNotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        "notification_type",
        "period_started_at",
        "status",
        "entry_count",
        "sent_at",
        "updated_at",
    )
    list_filter = ("notification_type", "status")
    readonly_fields = (
        "notification_type",
        "period_started_at",
        "status",
        "entry_count",
        "detail",
        "created_at",
        "updated_at",
        "sent_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
