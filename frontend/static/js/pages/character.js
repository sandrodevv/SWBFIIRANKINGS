import { getCharacter, getAllCharacterRankings, getVoteStatus } from "../api/client.js";
import { bindVoting, setVoteButtonsEnabled } from "../events/voting.js";
import { renderInlineRankings } from "../render/inline-rankings.js";
import { renderLeaderboard } from "../render/leaderboard.js";
import { renderPodium } from "../render/podium.js";
import { createCharacterImage, createBadge } from "../render/character-card.js";
import { nameEffectsFrom, renderPlayerName } from "../render/player-name.js";
import { getSlugFromPath, formatNumber } from "../utils/format.js";
import { showError, showLoading, createElement, clearElement } from "../utils/dom.js";

let currentSlug = null;
let characterSide = null;
let voteStatus = { can_vote: true };

function renderVoteStatusBanner(status) {
  let banner = document.querySelector('[data-container="vote-status"]');
  if (!banner) {
    banner = createElement("div", "vote-status-banner");
    banner.dataset.container = "vote-status";
    const main = document.querySelector(".site-main");
    if (main) {
      main.insertBefore(banner, main.firstChild);
    }
  }

  clearElement(banner);

  if (status.can_vote) {
    banner.hidden = true;
    return;
  }

  banner.hidden = false;
  banner.className = "vote-status-banner vote-status-banner--locked";

  const title = createElement("p", "vote-status-title", "Weekly vote used");
  const message = createElement("p", "vote-status-message");
  if (status.message) {
    message.textContent = status.message;
  } else if (status.last_voted_player) {
    message.appendChild(document.createTextNode("You already voted for "));
    message.appendChild(
      renderPlayerName(
        status.last_voted_player,
        status.last_voted_username,
        characterSide,
        "span",
        null,
        nameEffectsFrom(status)
      )
    );
    message.appendChild(document.createTextNode(". Come back next week."));
  } else {
    message.textContent = "You already voted for a player. Come back next week.";
  }
  banner.append(title, message);
}

async function loadVoteStatus() {
  if (!currentSlug) return;

  try {
    voteStatus = await getVoteStatus(currentSlug);
    renderVoteStatusBanner(voteStatus);

    const main = document.querySelector(".site-main");
    if (main && !voteStatus.can_vote) {
      setVoteButtonsEnabled(main, false);
    }
  } catch (error) {
    console.error("Failed to load vote status:", error);
  }
}

async function loadCharacterHeader({ showLoader = true } = {}) {
  const container = document.querySelector('[data-container="character-header"]');
  if (!container || !currentSlug) return;

  if (showLoader) showLoading(container);

  try {
    const character = await getCharacter(currentSlug);
    characterSide = character.side;
    clearElement(container);

    const inner = createElement("div", "character-header-inner");

    const imageWrap = createElement("div", "character-header-image");
    imageWrap.appendChild(
      createCharacterImage(character.name, character.side, character.image_url)
    );

    const info = createElement("div", "character-header-info");
    info.appendChild(createElement("h1", null, character.name));

    const meta = createElement("div", "card-meta");
    meta.appendChild(createBadge(character.side));
    info.appendChild(meta);

    if (character.description) {
      const desc = createElement("p", "text-muted", character.description);
      info.appendChild(desc);
    }

    const stats = createElement("div", "character-stats");

    const votesStat = createElement("div", "stat-item");
    votesStat.innerHTML = `<span class="stat-value" data-stat="total-votes">${formatNumber(character.total_votes)}</span><span class="stat-label">Total Votes</span>`;

    const playersStat = createElement("div", "stat-item");
    playersStat.innerHTML = `<span class="stat-value" data-stat="ranked-players">${formatNumber(character.ranked_player_count)}</span><span class="stat-label">Ranked Players</span>`;

    stats.append(votesStat, playersStat);
    info.appendChild(stats);

    inner.append(imageWrap, info);
    container.appendChild(inner);

    document.title = `${character.name} Rankings — BFII Player Rankings`;
  } catch (error) {
    showError(container, "Character not found.");
    console.error(error);
  }
}

async function refreshCharacterStats() {
  if (!currentSlug) return;

  try {
    const character = await getCharacter(currentSlug);
    const totalVotesEl = document.querySelector('[data-stat="total-votes"]');
    if (totalVotesEl) {
      totalVotesEl.textContent = formatNumber(character.total_votes);
    }
    const rankedPlayersEl = document.querySelector('[data-stat="ranked-players"]');
    if (rankedPlayersEl) {
      rankedPlayersEl.textContent = formatNumber(character.ranked_player_count);
    }
  } catch (error) {
    console.error("Failed to refresh character stats:", error);
  }
}

async function loadRankings() {
  const podiumContainer = document.querySelector('[data-container="podium"]');
  const leaderboardContainer = document.querySelector('[data-container="leaderboard"]');
  const inlineContainer = document.querySelector('[data-container="inline-rankings"]');
  if (!podiumContainer || !leaderboardContainer || !currentSlug) return;

  showLoading(podiumContainer, "Loading rankings...");
  showLoading(leaderboardContainer);
  if (inlineContainer) showLoading(inlineContainer);

  try {
    const rankings = await getAllCharacterRankings(currentSlug);

    renderPodium(rankings, podiumContainer);
    renderLeaderboard(rankings, leaderboardContainer);
    if (inlineContainer) {
      renderInlineRankings(rankings, inlineContainer);
    }

    if (!voteStatus.can_vote) {
      const main = document.querySelector(".site-main");
      if (main) setVoteButtonsEnabled(main, false);
    }
  } catch (error) {
    renderPodium([], podiumContainer);
    renderLeaderboard([], leaderboardContainer);
    if (inlineContainer) {
      renderInlineRankings([], inlineContainer);
    }
    console.error(error);
  }
}

async function refreshRankings() {
  await Promise.all([loadVoteStatus(), loadRankings(), refreshCharacterStats()]);
}

export function initCharacterPage() {
  currentSlug = getSlugFromPath();
  if (!currentSlug) return;

  loadCharacterHeader();
  loadVoteStatus().then(() => loadRankings());

  const main = document.querySelector(".site-main");
  if (main) {
    bindVoting(main, refreshRankings, (status) => {
      voteStatus = { ...voteStatus, ...status, can_vote: false };
      renderVoteStatusBanner(voteStatus);
    });
  }
}
