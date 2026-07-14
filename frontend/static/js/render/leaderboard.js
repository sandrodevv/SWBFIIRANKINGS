import { formatNumber } from "../utils/format.js";
import { createElement } from "../utils/dom.js";
import { nameEffectsFrom, renderPlayerName } from "./player-name.js";

export function renderLeaderboardRow(ranking) {
  const row = createElement("article", "leaderboard-row");
  row.dataset.rankingId = ranking.id;

  const rank = createElement("span", "leaderboard-rank", String(ranking.rank));
  const name = createElement("span", "leaderboard-name");
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
  const votes = createElement("span", "leaderboard-votes");
  votes.innerHTML = `<strong>${formatNumber(ranking.votes)}</strong> votes`;

  const voteBtn = createElement("button", "btn btn-vote", "Vote");
  voteBtn.type = "button";
  voteBtn.dataset.rankingId = ranking.id;

  row.append(rank, name, votes, voteBtn);
  return row;
}

export function renderLeaderboard(rankings, container) {
  container.replaceChildren();

  if (!rankings.length) {
    container.appendChild(
      createElement("div", "empty-state", "No players ranked yet.")
    );
    return;
  }

  const rest = rankings.filter((r) => r.rank >= 4 && r.rank <= 10);
  if (!rest.length) {
    container.appendChild(
      createElement("div", "empty-state", "No players in ranks 4–10 yet.")
    );
    return;
  }

  rest.forEach((ranking) => {
    container.appendChild(renderLeaderboardRow(ranking));
  });
}
