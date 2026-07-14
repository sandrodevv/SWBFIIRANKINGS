import { formatRelativeTime } from "../utils/format.js";
import { createElement } from "../utils/dom.js";
import { nameEffectsFrom, renderPlayerName } from "./player-name.js";

export function renderRecentVoteItem(vote) {
  const item = createElement("article", `recent-vote-item recent-vote-item--${vote.character_side}`);

  const body = createElement("div", "recent-vote-body");
  body.appendChild(
    renderPlayerName(
      vote.player_nickname,
      vote.player_username,
      vote.character_side,
      "span",
      vote.player_slug,
      nameEffectsFrom(vote)
    )
  );
  body.appendChild(document.createTextNode(" got voted for "));

  const characterLink = createElement("a", "recent-vote-character", vote.character_name);
  characterLink.href = `/characters/${vote.character_slug}/`;
  body.appendChild(characterLink);

  const time = createElement("time", "recent-vote-time");
  time.dateTime = vote.voted_at;
  time.textContent = formatRelativeTime(vote.voted_at);

  item.append(body, time);
  return item;
}

export function renderRecentVotes(votes, container) {
  container.replaceChildren();

  if (!votes.length) {
    container.appendChild(createElement("p", "recent-votes-empty", "No votes yet."));
    return;
  }

  votes.forEach((vote) => {
    container.appendChild(renderRecentVoteItem(vote));
  });
}
