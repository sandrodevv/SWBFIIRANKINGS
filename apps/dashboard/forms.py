from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Count, Q

from apps.characters.models import Character
from apps.rankings.models import Duelist, Player


class DashboardLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "username", "placeholder": "Username"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "placeholder": "Password"}),
    )


class AddPlayerWithAssignmentsForm(forms.Form):
    nickname = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "Player nickname"}),
    )
    username = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Optional platform username"}),
    )
    discord_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={"placeholder": "https://discord.com/users/..."}),
        label="Discord URL (optional)",
    )
    steam_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={"placeholder": "https://steamcommunity.com/id/..."}),
        label="Steam URL (optional)",
    )
    twitch_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={"placeholder": "https://twitch.tv/..."}),
        label="Twitch URL (optional)",
    )
    youtube_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={"placeholder": "https://youtube.com/@..."}),
        label="YouTube URL (optional)",
    )
    register_character_rankings = forms.BooleanField(
        required=False,
        initial=True,
        label="Register for Hero & Villain rankings",
    )
    hero_character = forms.ModelChoiceField(
        queryset=Character.objects.filter(side=Character.SIDE_HERO).order_by("name"),
        empty_label="Select a Hero",
        label="Hero character",
        required=False,
    )
    villain_character = forms.ModelChoiceField(
        queryset=Character.objects.filter(side=Character.SIDE_VILLAIN).order_by("name"),
        empty_label="Select a Villain",
        label="Villain character",
        required=False,
    )
    register_duelist = forms.BooleanField(
        required=False,
        initial=False,
        label="Register as Best Duelist",
    )
    duelist_region = forms.ChoiceField(
        choices=[("", "Select region")] + list(Duelist.REGION_CHOICES),
        label="Duelist region",
        required=False,
    )
    duelist_character = forms.ModelChoiceField(
        queryset=Character.saber_queryset(),
        empty_label="Select a Saber Hero",
        label="Duelist character (Saber only)",
        required=False,
    )

    def clean_nickname(self):
        nickname = self.cleaned_data["nickname"].strip()
        if not nickname:
            raise ValidationError("Nickname is required.")
        if Player.objects.filter(nickname__iexact=nickname).exists():
            raise ValidationError("A player with this nickname already exists.")
        return nickname

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        return username or None

    def clean_discord_url(self):
        value = (self.cleaned_data.get("discord_url") or "").strip()
        return value or ""

    def clean_steam_url(self):
        value = (self.cleaned_data.get("steam_url") or "").strip()
        return value or ""

    def clean_twitch_url(self):
        value = (self.cleaned_data.get("twitch_url") or "").strip()
        return value or ""

    def clean_youtube_url(self):
        value = (self.cleaned_data.get("youtube_url") or "").strip()
        return value or ""

    def clean(self):
        cleaned_data = super().clean()
        register_rankings = cleaned_data.get("register_character_rankings")
        register_duelist = cleaned_data.get("register_duelist")

        if not register_rankings and not register_duelist:
            raise ValidationError(
                "Select at least one option: Hero & Villain rankings, Best Duelist, or both."
            )

        if register_rankings:
            if not cleaned_data.get("hero_character"):
                self.add_error("hero_character", "Select a Hero character.")
            if not cleaned_data.get("villain_character"):
                self.add_error("villain_character", "Select a Villain character.")

        if register_duelist:
            if not cleaned_data.get("duelist_region"):
                self.add_error("duelist_region", "Select a region.")
            if not cleaned_data.get("duelist_character"):
                self.add_error("duelist_character", "Select the character this duelist represents.")

        return cleaned_data


def players_needing_assignment():
    return (
        Player.objects.annotate(
            hero_count=Count("rankings", filter=Q(rankings__character__side=Character.SIDE_HERO)),
            villain_count=Count(
                "rankings", filter=Q(rankings__character__side=Character.SIDE_VILLAIN)
            ),
            has_duelist=Count("duelist"),
        )
        .filter(Q(hero_count=0) | Q(villain_count=0) | Q(has_duelist=0))
        .order_by("nickname")
    )


class CompletePlayerAssignmentsForm(forms.Form):
    player = forms.ModelChoiceField(
        queryset=Player.objects.none(),
        empty_label="Select a player",
        label="Player",
    )
    assign_character_rankings = forms.BooleanField(
        required=False,
        initial=False,
        label="Assign Hero & Villain rankings",
    )
    hero_character = forms.ModelChoiceField(
        queryset=Character.objects.filter(side=Character.SIDE_HERO).order_by("name"),
        empty_label="Select a Hero",
        label="Hero character",
        required=False,
    )
    villain_character = forms.ModelChoiceField(
        queryset=Character.objects.filter(side=Character.SIDE_VILLAIN).order_by("name"),
        empty_label="Select a Villain",
        label="Villain character",
        required=False,
    )
    assign_duelist = forms.BooleanField(
        required=False,
        initial=False,
        label="Assign Best Duelist",
    )
    duelist_region = forms.ChoiceField(
        choices=[("", "Select region")] + list(Duelist.REGION_CHOICES),
        label="Duelist region",
        required=False,
    )
    duelist_character = forms.ModelChoiceField(
        queryset=Character.saber_queryset(),
        empty_label="Select a Saber Hero",
        label="Duelist character (Saber only)",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        players = players_needing_assignment()
        self.fields["player"].queryset = players
        self.player_flags = {
            str(player.pk): {
                "needs_rankings": player.hero_count == 0 or player.villain_count == 0,
                "needs_duelist": player.has_duelist == 0,
            }
            for player in players
        }

    def clean(self):
        cleaned_data = super().clean()
        player = cleaned_data.get("player")
        assign_rankings = cleaned_data.get("assign_character_rankings")
        assign_duelist = cleaned_data.get("assign_duelist")

        if not player:
            return cleaned_data

        has_hero = player.rankings.filter(character__side=Character.SIDE_HERO).exists()
        has_villain = player.rankings.filter(character__side=Character.SIDE_VILLAIN).exists()
        has_rankings = has_hero and has_villain
        has_duelist = hasattr(player, "duelist")

        if not assign_rankings and not assign_duelist:
            raise ValidationError(
                "Select at least one missing assignment to add for this player."
            )

        if assign_rankings:
            if has_rankings:
                self.add_error(
                    "assign_character_rankings",
                    f"{player.nickname} already has Hero & Villain rankings.",
                )
            else:
                if not cleaned_data.get("hero_character"):
                    self.add_error("hero_character", "Select a Hero character.")
                if not cleaned_data.get("villain_character"):
                    self.add_error("villain_character", "Select a Villain character.")

        if assign_duelist:
            if has_duelist:
                self.add_error(
                    "assign_duelist",
                    f"{player.nickname} is already registered as a Best Duelist.",
                )
            else:
                if not cleaned_data.get("duelist_region"):
                    self.add_error("duelist_region", "Select a region.")
                if not cleaned_data.get("duelist_character"):
                    self.add_error(
                        "duelist_character",
                        "Select the character this duelist represents.",
                    )

        return cleaned_data


def players_with_assignments():
    return (
        Player.objects.annotate(
            hero_count=Count("rankings", filter=Q(rankings__character__side=Character.SIDE_HERO)),
            villain_count=Count(
                "rankings", filter=Q(rankings__character__side=Character.SIDE_VILLAIN)
            ),
            has_duelist=Count("duelist"),
        )
        .filter(Q(hero_count__gt=0) | Q(villain_count__gt=0) | Q(has_duelist__gt=0))
        .order_by("nickname")
    )


class ModifyPlayerAssignmentsForm(forms.Form):
    player = forms.ModelChoiceField(
        queryset=Player.objects.none(),
        empty_label="Select a player",
        label="Player",
    )
    modify_character_rankings = forms.BooleanField(
        required=False,
        initial=False,
        label="Modify Hero & Villain rankings",
    )
    hero_character = forms.ModelChoiceField(
        queryset=Character.objects.filter(side=Character.SIDE_HERO).order_by("name"),
        empty_label="Select a Hero",
        label="Hero character",
        required=False,
    )
    villain_character = forms.ModelChoiceField(
        queryset=Character.objects.filter(side=Character.SIDE_VILLAIN).order_by("name"),
        empty_label="Select a Villain",
        label="Villain character",
        required=False,
    )
    modify_duelist = forms.BooleanField(
        required=False,
        initial=False,
        label="Modify Best Duelist",
    )
    duelist_region = forms.ChoiceField(
        choices=[("", "Select region")] + list(Duelist.REGION_CHOICES),
        label="Duelist region",
        required=False,
    )
    duelist_character = forms.ModelChoiceField(
        queryset=Character.saber_queryset(),
        empty_label="Select a Saber Hero",
        label="Duelist character (Saber only)",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        players = players_with_assignments().prefetch_related(
            "rankings__character",
            "duelist__character",
        )
        self.fields["player"].queryset = players
        self.player_assignments = {}
        for player in players:
            hero = next(
                (
                    ranking.character
                    for ranking in player.rankings.all()
                    if ranking.character.side == Character.SIDE_HERO
                ),
                None,
            )
            villain = next(
                (
                    ranking.character
                    for ranking in player.rankings.all()
                    if ranking.character.side == Character.SIDE_VILLAIN
                ),
                None,
            )
            duelist = getattr(player, "duelist", None)
            self.player_assignments[str(player.pk)] = {
                "has_rankings": hero is not None and villain is not None,
                "hero_id": hero.id if hero else None,
                "villain_id": villain.id if villain else None,
                "has_duelist": duelist is not None,
                "duelist_region": duelist.region if duelist else "",
                "duelist_character_id": duelist.character_id if duelist else None,
            }

    def clean(self):
        cleaned_data = super().clean()
        player = cleaned_data.get("player")
        modify_rankings = cleaned_data.get("modify_character_rankings")
        modify_duelist = cleaned_data.get("modify_duelist")

        if not player:
            return cleaned_data

        info = self.player_assignments.get(str(player.pk), {})

        if not modify_rankings and not modify_duelist:
            raise ValidationError("Select at least one assignment to modify.")

        if modify_rankings:
            if not info.get("has_rankings"):
                self.add_error(
                    "modify_character_rankings",
                    f"{player.nickname} does not have Hero & Villain rankings.",
                )
            else:
                if not cleaned_data.get("hero_character"):
                    self.add_error("hero_character", "Select a Hero character.")
                if not cleaned_data.get("villain_character"):
                    self.add_error("villain_character", "Select a Villain character.")

        if modify_duelist:
            if not info.get("has_duelist"):
                self.add_error(
                    "modify_duelist",
                    f"{player.nickname} is not registered as a Best Duelist.",
                )
            else:
                if not cleaned_data.get("duelist_region"):
                    self.add_error("duelist_region", "Select a region.")
                if not cleaned_data.get("duelist_character"):
                    self.add_error(
                        "duelist_character",
                        "Select the character this duelist represents.",
                    )

        return cleaned_data


class NameEffectsForm(forms.Form):
    player = forms.ModelChoiceField(
        queryset=Player.objects.none(),
        empty_label="Select a player",
        label="Player",
    )
    name_burning = forms.BooleanField(
        required=False,
        initial=False,
        label="Burning nickname",
    )
    name_smoke = forms.BooleanField(
        required=False,
        initial=False,
        label="Smoke nickname",
    )
    name_glitch = forms.BooleanField(
        required=False,
        initial=False,
        label="Glitch nickname",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        players = Player.objects.order_by("nickname")
        self.fields["player"].queryset = players
        self.player_effects = {
            str(player.pk): {
                "burning": bool(player.name_burning),
                "smoke": bool(player.name_smoke),
                "glitch": bool(player.name_glitch),
            }
            for player in players
        }


class PlayerLinksForm(forms.Form):
    player = forms.ModelChoiceField(
        queryset=Player.objects.none(),
        empty_label="Select a player",
        label="Player",
    )
    discord_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "https://discord.com/users/..."}),
        label="Discord URL",
    )
    steam_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "https://steamcommunity.com/id/..."}),
        label="Steam URL",
    )
    twitch_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "https://twitch.tv/..."}),
        label="Twitch URL",
    )
    youtube_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "https://youtube.com/@..."}),
        label="YouTube URL",
    )
    clear_discord = forms.BooleanField(
        required=False,
        initial=False,
        label="Remove Discord link",
    )
    clear_steam = forms.BooleanField(
        required=False,
        initial=False,
        label="Remove Steam link",
    )
    clear_twitch = forms.BooleanField(
        required=False,
        initial=False,
        label="Remove Twitch link",
    )
    clear_youtube = forms.BooleanField(
        required=False,
        initial=False,
        label="Remove YouTube link",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        players = Player.objects.order_by("nickname")
        self.fields["player"].queryset = players
        self.player_links = {
            str(player.pk): {
                "discord_url": player.discord_url or "",
                "steam_url": player.steam_url or "",
                "twitch_url": player.twitch_url or "",
                "youtube_url": player.youtube_url or "",
            }
            for player in players
        }

    def clean_discord_url(self):
        value = (self.cleaned_data.get("discord_url") or "").strip()
        if not value:
            return ""
        validator = forms.URLField().clean
        return validator(value)

    def clean_steam_url(self):
        value = (self.cleaned_data.get("steam_url") or "").strip()
        if not value:
            return ""
        validator = forms.URLField().clean
        return validator(value)

    def clean_twitch_url(self):
        value = (self.cleaned_data.get("twitch_url") or "").strip()
        if not value:
            return ""
        validator = forms.URLField().clean
        return validator(value)

    def clean_youtube_url(self):
        value = (self.cleaned_data.get("youtube_url") or "").strip()
        if not value:
            return ""
        validator = forms.URLField().clean
        return validator(value)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("clear_discord"):
            cleaned_data["discord_url"] = ""
        if cleaned_data.get("clear_steam"):
            cleaned_data["steam_url"] = ""
        if cleaned_data.get("clear_twitch"):
            cleaned_data["twitch_url"] = ""
        if cleaned_data.get("clear_youtube"):
            cleaned_data["youtube_url"] = ""
        return cleaned_data
