import { formatNumber } from "../utils/format.js";
import { createElement } from "../utils/dom.js";
import { nameEffectsFrom, renderPlayerName } from "./player-name.js";

const PODIUM_CONFIG = {
  1: { className: "podium-first",  },
  2: { className: "podium-second",  },
  3: { className: "podium-third",  },
};

export function renderPodiumCard(ranking) {
  const config = PODIUM_CONFIG[ranking.rank] || PODIUM_CONFIG[3];
  const card = createElement("article", `podium-card ${config.className}`);
  card.dataset.rankingId = ranking.id;

  const rankEl = createElement("div", "podium-rank", ` ${ranking.rank === 1 ? "First Place" : ranking.rank === 2 ? "Second Place" : "Third Place"}`);
  const playerEl = createElement("div", "podium-player");
  playerEl.appendChild(
    renderPlayerName(
      ranking.nickname,
      ranking.username,
      ranking.character_side,
      "span",
      ranking.player_slug,
      nameEffectsFrom(ranking)
    )
  );
  const votesEl = createElement("div", "podium-votes");
  votesEl.innerHTML = `<strong>${formatNumber(ranking.votes)}</strong> votes`;

  const actions = createElement("div", "podium-actions");
  const voteBtn = createElement("button", "btn btn-vote", "Vote");
  voteBtn.type = "button";
  voteBtn.dataset.rankingId = ranking.id;
  actions.appendChild(voteBtn);

  card.append(rankEl, playerEl, votesEl, actions);
  return card;
}

export function renderPodium(rankings, container) {
  container.replaceChildren();

  const topThree = rankings.filter((r) => r.rank <= 3);
  if (!topThree.length) {
    container.appendChild(
      createElement("div", "empty-state", "No players ranked yet.")
    );
    return;
  }

  const order = [2, 1, 3];
  const sorted = order
    .map((rank) => topThree.find((r) => r.rank === rank))
    .filter(Boolean);

  sorted.forEach((ranking) => {
    container.appendChild(renderPodiumCard(ranking));
  });
}
