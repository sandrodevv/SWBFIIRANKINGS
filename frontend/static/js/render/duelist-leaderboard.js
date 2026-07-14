import { formatNumber } from "../utils/format.js";
import { createElement } from "../utils/dom.js";
import { nameEffectsFrom, renderPlayerName } from "./player-name.js";
import { createBadge } from "./character-card.js";

export const DUELIST_PANEL_LIMIT = 16;

const TOP_ROW_CLASS = {
  1: "duelist-row--first",
  2: "duelist-row--second",
  3: "duelist-row--third",
};

export function renderDuelistRow(entry, { showVote = true, period = "weekly", compact = false } = {}) {
  const topClass = TOP_ROW_CLASS[entry.rank] || "";
  const rowClass = compact
    ? `inline-ranking-item duelist-inline-item duelist-inline-item--${entry.character_side}`
    : `duelist-row duelist-row--${entry.character_side} ${topClass}`.trim();
  const row = createElement("article", rowClass);
  row.dataset.duelistId = entry.id;
  row.dataset.region = entry.region;
  const effect = nameEffectsFrom(entry);

  const rank = createElement(
    "span",
    compact ? "inline-ranking-rank" : "duelist-rank",
    `#${entry.rank}`
  );

  if (compact) {
    const name = createElement("span", "inline-ranking-name");
    name.appendChild(
      renderPlayerName(
        entry.nickname,
        entry.username,
        entry.character_side,
        "span",
        entry.slug,
        effect
      )
    );

    const character = createElement("span", "duelist-inline-character");
    const link = createElement("a", null, entry.character_name);
    link.href = `/characters/${entry.character_slug}/`;
    character.append(link, createBadge(entry.character_side));

    const region = createElement("span", "duelist-region", entry.region_label);

    const voteCount = period === "all_time" ? entry.all_time_votes : entry.votes;
    const voteLabel = period === "all_time" ? "all-time" : "weekly";
    const votes = createElement("span", "inline-ranking-votes");
    votes.innerHTML = `<strong>${formatNumber(voteCount)}</strong> ${voteLabel}`;

    row.append(rank, name, character, region, votes);

    if (showVote) {
      const voteBtn = createElement("button", "btn btn-vote btn-vote-inline", "Vote");
      voteBtn.type = "button";
      voteBtn.dataset.duelistId = entry.id;
      row.appendChild(voteBtn);
    }

    return row;
  }

  const main = createElement("div", "duelist-main");
  const player = createElement("div", "duelist-player");
  player.appendChild(
    renderPlayerName(
      entry.nickname,
      entry.username,
      entry.character_side,
      "span",
      entry.slug,
      effect
    )
  );

  const character = createElement("div", "duelist-character");
  const link = createElement("a", null, entry.character_name);
  link.href = `/characters/${entry.character_slug}/`;
  character.appendChild(link);

  const region = createElement("span", "duelist-region", entry.region_label);
  character.appendChild(region);

  main.append(player, character);

  const voteCount = period === "all_time" ? entry.all_time_votes : entry.votes;
  const voteLabel = period === "all_time" ? "all-time" : "weekly";
  const votes = createElement("div", "duelist-votes");
  votes.innerHTML = `<strong>${formatNumber(voteCount)}</strong><span>${voteLabel}</span>`;

  row.append(rank, main, votes);

  if (showVote) {
    const voteBtn = createElement("button", "btn btn-vote", "Vote");
    voteBtn.type = "button";
    voteBtn.dataset.duelistId = entry.id;
    row.appendChild(voteBtn);
  }

  return row;
}

export function renderDuelistLeaderboard(entries, container, options = {}) {
  container.replaceChildren();

  const topEntries = entries.filter((entry) => entry.rank <= DUELIST_PANEL_LIMIT);

  if (!topEntries.length) {
    container.appendChild(createElement("div", "empty-state", "No duelist rankings yet."));
    return;
  }

  topEntries.forEach((entry) => {
    container.appendChild(renderDuelistRow(entry, options));
  });
}

export function renderDuelistInlineRankings(entries, container, options = {}) {
  container.replaceChildren();

  const rest = entries.filter((entry) => entry.rank > DUELIST_PANEL_LIMIT);
  const section = container.closest(".duelist-inline-section");

  if (!rest.length) {
    if (section) section.hidden = true;
    return;
  }

  if (section) section.hidden = false;

  rest.forEach((entry) => {
    container.appendChild(
      renderDuelistRow(entry, {
        ...options,
        compact: true,
      })
    );
  });
}
