import { formatNumber } from "../utils/format.js";
import { createElement } from "../utils/dom.js";
import { nameEffectsFrom, renderPlayerName } from "./player-name.js";
import { createBadge } from "./character-card.js";

const TOP_ROW_CLASS = {
  1: "pfp-row--first",
  2: "pfp-row--second",
  3: "pfp-row--third",
};

export function renderPfpRow(entry) {
  const topClass = TOP_ROW_CLASS[entry.global_rank] || "";
  const row = createElement(
    "article",
    `pfp-row pfp-row--${entry.character_side} ${topClass}`.trim()
  );

  const rank = createElement("span", "pfp-rank", `#${entry.global_rank}`);
  const score = createElement("div", "pfp-score");
  score.innerHTML = `<span class="pfp-score-value">${entry.pfp_score.toFixed(2)}</span><span class="pfp-score-label">PFP</span>`;

  const main = createElement("div", "pfp-main");
  const player = createElement("div", "pfp-player");
  player.appendChild(
    renderPlayerName(
      entry.player_nickname,
      entry.player_username,
      entry.character_side,
      "span",
      entry.player_slug,
      nameEffectsFrom(entry)
    )
  );

  const character = createElement("div", "pfp-character");
  const link = createElement("a", null, entry.character_name);
  link.href = `/characters/${entry.character_slug}/`;
  character.appendChild(link);
  character.appendChild(createBadge(entry.character_side));

  main.append(player, character);

  const meta = createElement("div", "pfp-meta");
  meta.innerHTML = `<span>Character rank <strong>#${entry.character_rank}</strong></span><span>${formatNumber(entry.all_time_votes)} all-time votes</span>`;

  row.append(rank, score, main, meta);
  return row;
}

export function renderPfpLeaderboard(entries, container) {
  container.replaceChildren();

  if (!entries.length) {
    container.appendChild(createElement("div", "empty-state", "No PFP rankings yet."));
    return;
  }

  entries.forEach((entry) => {
    container.appendChild(renderPfpRow(entry));
  });
}
