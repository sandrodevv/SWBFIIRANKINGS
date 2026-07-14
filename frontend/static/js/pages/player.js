import { getPlayer } from "../api/client.js";
import { createBadge } from "../render/character-card.js";
import { nameEffectsFrom, renderPlayerName } from "../render/player-name.js";
import { getPlayerSlugFromPath, formatNumber } from "../utils/format.js";
import { showError, showLoading, createElement, clearElement } from "../utils/dom.js";

function renderAssignmentCard(assignment, label) {
  const card = createElement(
    "article",
    `player-assignment-card player-assignment-card--${assignment.side}`
  );

  const header = createElement("div", "player-assignment-header");
  header.appendChild(createElement("span", "player-assignment-label", label));
  header.appendChild(createBadge(assignment.side));
  card.appendChild(header);

  const title = createElement("h3", "player-assignment-title");
  const link = createElement("a", null, assignment.character_name);
  link.href = `/characters/${assignment.character_slug}/`;
  title.appendChild(link);
  card.appendChild(title);

  const stats = createElement("div", "player-assignment-stats");
  stats.innerHTML = `
    <div class="stat-item">
      <span class="stat-value">#${assignment.rank ?? "—"}</span>
      <span class="stat-label">Rank</span>
    </div>
    <div class="stat-item">
      <span class="stat-value">${formatNumber(assignment.weekly_votes)}</span>
      <span class="stat-label">This Week</span>
    </div>
    <div class="stat-item">
      <span class="stat-value">${formatNumber(assignment.all_time_votes)}</span>
      <span class="stat-label">All Time</span>
    </div>
  `;
  card.appendChild(stats);

  return card;
}

function renderEmptyAssignment(label) {
  const card = createElement("article", "player-assignment-card player-assignment-card--empty");
  card.appendChild(createElement("span", "player-assignment-label", label));
  card.appendChild(createElement("p", "text-muted", "Player is not assigned to any character yet."));
  return card;
}

function renderDuelistCard(duelist) {
  const card = createElement(
    "article",
    `player-assignment-card player-assignment-card--duelist player-assignment-card--${duelist.character_side}`
  );

  const header = createElement("div", "player-assignment-header");
  header.appendChild(createElement("span", "player-assignment-label", "Duelist Rank"));
  const meta = createElement("div", "player-duelist-meta");
  meta.appendChild(createElement("span", "duelist-region", duelist.region_label));
  meta.appendChild(createBadge(duelist.character_side));
  header.appendChild(meta);
  card.appendChild(header);

  const title = createElement("h3", "player-assignment-title");
  const link = createElement("a", null, duelist.character_name);
  link.href = `/characters/${duelist.character_slug}/`;
  title.appendChild(link);
  card.appendChild(title);

  const stats = createElement("div", "player-assignment-stats");
  stats.innerHTML = `
    <div class="stat-item">
      <span class="stat-value">#${duelist.region_rank ?? "—"}</span>
      <span class="stat-label">${duelist.region_label} Rank</span>
    </div>
    <div class="stat-item">
      <span class="stat-value">#${duelist.overall_rank ?? "—"}</span>
      <span class="stat-label">Overall Rank</span>
    </div>
    <div class="stat-item">
      <span class="stat-value">${formatNumber(duelist.weekly_votes)}</span>
      <span class="stat-label">This Week</span>
    </div>
    <div class="stat-item">
      <span class="stat-value">${formatNumber(duelist.all_time_votes)}</span>
      <span class="stat-label">All Time</span>
    </div>
  `;
  card.appendChild(stats);

  const footer = createElement("div", "player-duelist-footer");
  const boardLink = createElement("a", "player-duelist-link", "View duelist leaderboard");
  boardLink.href = "/duelists/";
  footer.appendChild(boardLink);
  card.appendChild(footer);

  return card;
}

function renderEmptyDuelist() {
  const card = createElement("article", "player-assignment-card player-assignment-card--empty");
  card.appendChild(createElement("span", "player-assignment-label", "Duelist Rank"));
  card.appendChild(createElement("p", "text-muted", "Not registered as a duelist."));
  return card;
}

async function loadPlayerProfile() {
  const slug = getPlayerSlugFromPath();
  const headerContainer = document.querySelector('[data-container="player-header"]');
  const assignmentsContainer = document.querySelector('[data-container="player-assignments"]');
  const duelistContainer = document.querySelector('[data-container="player-duelist"]');

  if (!slug || !headerContainer || !assignmentsContainer || !duelistContainer) return;

  showLoading(headerContainer);
  showLoading(assignmentsContainer);
  showLoading(duelistContainer);

  try {
    const player = await getPlayer(slug);
    clearElement(headerContainer);

    const inner = createElement("div", "player-header-inner");
    const identity = createElement("div", "player-header-identity");
    identity.appendChild(
      renderPlayerName(
        player.nickname,
        player.username,
        null,
        "span",
        null,
        nameEffectsFrom(player)
      )
    );

    if (player.discord_url || player.steam_url || player.twitch_url) {
      const socials = createElement("div", "player-socials");
      if (player.discord_url) {
        const discord = createElement("a", "player-social-link player-social-link--discord");
        discord.href = player.discord_url;
        discord.target = "_blank";
        discord.rel = "noopener noreferrer";
        discord.title = "Discord";
        discord.setAttribute("aria-label", `${player.nickname} on Discord`);
        discord.innerHTML = '<i class="fa-brands fa-discord" aria-hidden="true"></i>';
        socials.appendChild(discord);
      }
      if (player.steam_url) {
        const steam = createElement("a", "player-social-link player-social-link--steam");
        steam.href = player.steam_url;
        steam.target = "_blank";
        steam.rel = "noopener noreferrer";
        steam.title = "Steam";
        steam.setAttribute("aria-label", `${player.nickname} on Steam`);
        steam.innerHTML = '<i class="fa-brands fa-steam" aria-hidden="true"></i>';
        socials.appendChild(steam);
      }
      if (player.twitch_url) {
        const twitch = createElement("a", "player-social-link player-social-link--twitch");
        twitch.href = player.twitch_url;
        twitch.target = "_blank";
        twitch.rel = "noopener noreferrer";
        twitch.title = "Twitch";
        twitch.setAttribute("aria-label", `${player.nickname} on Twitch`);
        twitch.innerHTML = '<i class="fa-brands fa-twitch" aria-hidden="true"></i>';
        socials.appendChild(twitch);
      }
      identity.appendChild(socials);
    }

    const stats = createElement("div", "player-stats");
    stats.innerHTML = `
      <div class="stat-item">
        <span class="stat-value">${formatNumber(player.weekly_votes)}</span>
        <span class="stat-label">This Week</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">${formatNumber(player.all_time_votes)}</span>
        <span class="stat-label">All Time</span>
      </div>
    `;

    inner.append(identity, stats);
    headerContainer.appendChild(inner);

    clearElement(assignmentsContainer);
    assignmentsContainer.appendChild(
      player.hero_assignment
        ? renderAssignmentCard(player.hero_assignment, "Hero")
        : renderEmptyAssignment("Hero")
    );
    assignmentsContainer.appendChild(
      player.villain_assignment
        ? renderAssignmentCard(player.villain_assignment, "Villain")
        : renderEmptyAssignment("Villain")
    );

    clearElement(duelistContainer);
    duelistContainer.appendChild(
      player.duelist ? renderDuelistCard(player.duelist) : renderEmptyDuelist()
    );

    document.title = `${player.nickname} — BFII Player Rankings`;
  } catch (error) {
    showError(headerContainer, "Player not found.");
    clearElement(assignmentsContainer);
    clearElement(duelistContainer);
    console.error(error);
  }
}

export function initPlayerPage() {
  if (!getPlayerSlugFromPath()) return;
  loadPlayerProfile();
}
