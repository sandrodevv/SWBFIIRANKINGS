import { formatNumber } from "../utils/format.js";
import { nameEffectsFrom, formatPlayerNameHtml } from "./player-name.js";
import {
  createCharacterImage,
  createBadge,
  createViewRankingsButton,
} from "./character-card.js";
import { createElement } from "../utils/dom.js";

export function renderChampionCard(champion) {
  const card = document.createElement("article");
  card.className = `champion-card champion-card--${champion.character_side}`;

  card.appendChild(
    createCharacterImage(
      champion.character_name,
      champion.character_side,
      champion.image_url
    )
  );

  const body = createElement("div", "card-body");

  const label = createElement("div", "champion-label");
  label.innerHTML = "Current Champion";

  const title = createElement("h3", "card-title", champion.character_name);

  const meta = createElement("div", "card-meta");
  meta.appendChild(createBadge(champion.character_side));


  const playerStat = createElement("p", "card-stat");
  playerStat.innerHTML = `${formatPlayerNameHtml(champion.player_nickname, champion.player_username, champion.character_side, champion.player_slug, nameEffectsFrom(champion))} · ${formatNumber(champion.votes)} votes`;




  const actions = createElement("div", "card-actions");
  actions.appendChild(createViewRankingsButton(champion.character_slug, champion.character_side));

  body.append(label, title, meta, playerStat, actions);
  card.appendChild(body);
  return card;
}
