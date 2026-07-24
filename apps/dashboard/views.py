from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .bruteforce import clear_failed_logins, is_login_locked, lockout_minutes, record_failed_login
from .decorators import staff_required
from .forms import (
    AddPlayerWithAssignmentsForm,
    CompletePlayerAssignmentsForm,
    DashboardLoginForm,
    ModifyPlayerAssignmentsForm,
    NameEffectsForm,
    PlayerLinksForm,
)
from .models import ModeratorLoginLog
from .overview import get_admin_overview
from .services import (
    complete_player_assignments,
    create_player_with_assignments,
    modify_player_assignments,
    set_player_links,
    set_player_name_effects,
)
from .utils import get_client_ip


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard-home")

    form = DashboardLoginForm(request.POST or None)
    ip = get_client_ip(request)

    if request.method == "POST":
        if is_login_locked(ip):
            messages.error(
                request,
                f"Too many failed login attempts. Try again in about {lockout_minutes()} minutes.",
            )
            return render(request, "dashboard/login.html", {"form": form, "locked_out": True})

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is None or not user.is_staff:
            record_failed_login(ip)
            if is_login_locked(ip):
                messages.error(
                    request,
                    f"Too many failed login attempts. Try again in about {lockout_minutes()} minutes.",
                )
            elif user is not None and not user.is_staff:
                messages.error(request, "You do not have moderator access.")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            clear_failed_logins(ip)
            login(request, user)
            if ip:
                ModeratorLoginLog.objects.create(
                    user=user,
                    ip_address=ip,
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
                )
            return redirect("dashboard-home")

    return render(request, "dashboard/login.html", {"form": form})


@require_http_methods(["POST"])
@staff_required
def logout_view(request):
    logout(request)
    return redirect("dashboard-login")


def _build_add_success_message(player, cleaned_data):
    parts = []
    if cleaned_data.get("register_character_rankings"):
        hero = cleaned_data["hero_character"]
        villain = cleaned_data["villain_character"]
        parts.append(f"{hero.name} (Hero) and {villain.name} (Villain)")
    if cleaned_data.get("register_duelist"):
        character = cleaned_data["duelist_character"]
        region = cleaned_data["duelist_region"].upper()
        parts.append(f"Best Duelist as {character.name} ({region})")
    detail = " and ".join(parts)
    return f"Added {player.nickname} — {detail}."


def _build_complete_success_message(player, cleaned_data):
    parts = []
    if cleaned_data.get("assign_character_rankings"):
        hero = cleaned_data["hero_character"]
        villain = cleaned_data["villain_character"]
        parts.append(f"Hero & Villain ({hero.name} / {villain.name})")
    if cleaned_data.get("assign_duelist"):
        character = cleaned_data["duelist_character"]
        region = cleaned_data["duelist_region"].upper()
        parts.append(f"Best Duelist ({character.name}, {region})")
    detail = " and ".join(parts)
    return f"Updated {player.nickname} — added {detail}."


def _build_modify_success_message(player, cleaned_data, result):
    parts = []
    if result["hero_changed"] or result["villain_changed"]:
        hero = cleaned_data["hero_character"]
        villain = cleaned_data["villain_character"]
        reset_note = "votes reset" if (result["hero_changed"] or result["villain_changed"]) else ""
        parts.append(f"rankings → {hero.name} / {villain.name} ({reset_note})")
    if result["duelist_changed"]:
        character = cleaned_data["duelist_character"]
        region = cleaned_data["duelist_region"].upper()
        if result["duelist_votes_reset"]:
            parts.append(f"duelist → {character.name} ({region}, votes reset)")
        else:
            parts.append(f"duelist → {character.name} ({region})")
    detail = "; ".join(parts)
    return f"Modified {player.nickname} — {detail}."


def _apply_form_errors(form, exc):
    if hasattr(exc, "message_dict"):
        for field, errors in exc.message_dict.items():
            for error in errors:
                form.add_error(field if field in form.fields else None, error)
    elif hasattr(exc, "messages"):
        for error in exc.messages:
            form.add_error(None, error)
    else:
        form.add_error(None, str(exc))


@require_http_methods(["GET", "POST"])
@staff_required
def home_view(request):
    add_form = AddPlayerWithAssignmentsForm()
    complete_form = CompletePlayerAssignmentsForm()
    modify_form = ModifyPlayerAssignmentsForm(prefix="modify")
    burning_form = NameEffectsForm(prefix="effects")
    links_form = PlayerLinksForm(prefix="links")
    active_form = "add"
    is_admin = request.user.is_superuser

    if request.method == "POST":
        action = request.POST.get("form_action", "add")
        active_form = action

        if action == "links":
            links_form = PlayerLinksForm(request.POST, prefix="links")
            if links_form.is_valid():
                player, changed = set_player_links(
                    player=links_form.cleaned_data["player"],
                    discord_url=links_form.cleaned_data["discord_url"],
                    steam_url=links_form.cleaned_data["steam_url"],
                    twitch_url=links_form.cleaned_data["twitch_url"],
                    youtube_url=links_form.cleaned_data["youtube_url"],
                )
                if changed:
                    removed = []
                    if links_form.cleaned_data.get("clear_discord"):
                        removed.append("Discord")
                    if links_form.cleaned_data.get("clear_steam"):
                        removed.append("Steam")
                    if links_form.cleaned_data.get("clear_twitch"):
                        removed.append("Twitch")
                    if links_form.cleaned_data.get("clear_youtube"):
                        removed.append("YouTube")
                    if removed:
                        messages.success(
                            request,
                            f"Removed {' and '.join(removed)} link(s) for {player.nickname}.",
                        )
                    else:
                        messages.success(
                            request,
                            f"Updated profile links for {player.nickname}.",
                        )
                else:
                    messages.info(request, f"No link changes for {player.nickname}.")
                return redirect("dashboard-home")
        elif action == "effects":
            if not is_admin:
                messages.error(request, "Only administrators can change nickname effects.")
                return redirect("dashboard-home")
            burning_form = NameEffectsForm(request.POST, prefix="effects")
            if burning_form.is_valid():
                player, changed = set_player_name_effects(
                    player=burning_form.cleaned_data["player"],
                    name_burning=burning_form.cleaned_data["name_burning"],
                    name_smoke=burning_form.cleaned_data["name_smoke"],
                    name_glitch=burning_form.cleaned_data["name_glitch"],
                )
                if changed:
                    parts = []
                    parts.append("burning on" if player.name_burning else "burning off")
                    parts.append("smoke on" if player.name_smoke else "smoke off")
                    parts.append("glitch on" if player.name_glitch else "glitch off")
                    messages.success(
                        request,
                        f"Name effects for {player.nickname}: {', '.join(parts)}.",
                    )
                else:
                    messages.info(
                        request,
                        f"No change for {player.nickname}.",
                    )
                return redirect("dashboard-home")
        elif action == "complete":
            complete_form = CompletePlayerAssignmentsForm(request.POST)
            if complete_form.is_valid():
                try:
                    player = complete_player_assignments(
                        player=complete_form.cleaned_data["player"],
                        assign_character_rankings=complete_form.cleaned_data[
                            "assign_character_rankings"
                        ],
                        hero_character=complete_form.cleaned_data.get("hero_character"),
                        villain_character=complete_form.cleaned_data.get("villain_character"),
                        assign_duelist=complete_form.cleaned_data["assign_duelist"],
                        duelist_region=complete_form.cleaned_data.get("duelist_region") or None,
                        duelist_character=complete_form.cleaned_data.get("duelist_character"),
                    )
                except ValidationError as exc:
                    _apply_form_errors(complete_form, exc)
                else:
                    messages.success(
                        request,
                        _build_complete_success_message(player, complete_form.cleaned_data),
                    )
                    return redirect("dashboard-home")
        elif action == "modify":
            modify_form = ModifyPlayerAssignmentsForm(request.POST, prefix="modify")
            if modify_form.is_valid():
                try:
                    player, result = modify_player_assignments(
                        player=modify_form.cleaned_data["player"],
                        modify_character_rankings=modify_form.cleaned_data[
                            "modify_character_rankings"
                        ],
                        hero_character=modify_form.cleaned_data.get("hero_character"),
                        villain_character=modify_form.cleaned_data.get("villain_character"),
                        modify_duelist=modify_form.cleaned_data["modify_duelist"],
                        duelist_region=modify_form.cleaned_data.get("duelist_region") or None,
                        duelist_character=modify_form.cleaned_data.get("duelist_character"),
                    )
                except ValidationError as exc:
                    _apply_form_errors(modify_form, exc)
                else:
                    messages.success(
                        request,
                        _build_modify_success_message(
                            player, modify_form.cleaned_data, result
                        ),
                    )
                    return redirect("dashboard-home")
        else:
            add_form = AddPlayerWithAssignmentsForm(request.POST)
            if add_form.is_valid():
                try:
                    player = create_player_with_assignments(
                        nickname=add_form.cleaned_data["nickname"],
                        username=add_form.cleaned_data["username"],
                        discord_url=add_form.cleaned_data.get("discord_url") or "",
                        steam_url=add_form.cleaned_data.get("steam_url") or "",
                        twitch_url=add_form.cleaned_data.get("twitch_url") or "",
                        youtube_url=add_form.cleaned_data.get("youtube_url") or "",
                        register_character_rankings=add_form.cleaned_data[
                            "register_character_rankings"
                        ],
                        hero_character=add_form.cleaned_data.get("hero_character"),
                        villain_character=add_form.cleaned_data.get("villain_character"),
                        register_duelist=add_form.cleaned_data["register_duelist"],
                        duelist_region=add_form.cleaned_data.get("duelist_region") or None,
                        duelist_character=add_form.cleaned_data.get("duelist_character"),
                    )
                except ValidationError as exc:
                    _apply_form_errors(add_form, exc)
                else:
                    messages.success(
                        request,
                        _build_add_success_message(player, add_form.cleaned_data),
                    )
                    return redirect("dashboard-home")

    context = {
        "form": add_form,
        "complete_form": complete_form,
        "modify_form": modify_form,
        "burning_form": burning_form,
        "links_form": links_form,
        "active_form": active_form,
        "player_flags": complete_form.player_flags,
        "player_assignments": modify_form.player_assignments,
        "player_effects": burning_form.player_effects,
        "player_links": links_form.player_links,
        "is_admin": is_admin,
        "overview": get_admin_overview(include_details=is_admin),
    }
    return render(request, "dashboard/home.html", context)
