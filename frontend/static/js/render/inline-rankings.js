import { formatNumber } from "../utils/format.js";
import { createElement } from "../utils/dom.js";
import { nameEffectsFrom, renderPlayerName } from "./player-name.js";

export function renderInlineRankingItem(ranking) {
  const item = createElement("article", "inline-ranking-item");
  item.dataset.rankingId = ranking.id;

  const rank = createElement("span", "inline-ranking-rank", `#${ranking.rank}`);
  const name = createElement("span", "inline-ranking-name");
  name.appendChild(
    renderPlayerName(
      ranking.nickname,
      ranking.username,
      ranking.character_side,
      "span",
      ranking.player_slug,
      nameEffectsFrom(ranking)
    )
  );
  const votes = createElement("span", "inline-ranking-votes");
  votes.innerHTML = `<strong>${formatNumber(ranking.votes)}</strong> votes`;

  const voteBtn = createElement("button", "btn btn-vote btn-vote-inline", "Vote");
  voteBtn.type = "button";
  voteBtn.dataset.rankingId = ranking.id;

  item.append(rank, name, votes, voteBtn);
  return item;
}

export function renderInlineRankings(rankings, container) {
  container.replaceChildren();

  const rest = rankings.filter((r) => r.rank >= 11);
  const section = container.closest(".inline-rankings-section");

  if (!rest.length) {
    if (section) section.hidden = true;
    return;
  }

  if (section) section.hidden = false;

  rest.forEach((ranking) => {
    container.appendChild(renderInlineRankingItem(ranking));
  });
}
