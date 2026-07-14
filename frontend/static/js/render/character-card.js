import { getInitials, sideLabel, formatNumber } from "../utils/format.js";
import { nameEffectsFrom, formatPlayerNameHtml } from "./player-name.js";

export function createCharacterImage(name, side, imageUrl) {
  const wrap = document.createElement("div");
  wrap.className = "card-image-wrap";

  const img = document.createElement("img");
  img.alt = name;
  img.loading = "lazy";
  img.src = imageUrl;

  const fallback = document.createElement("div");
  fallback.className = `card-image-fallback fallback-${side}`;
  fallback.textContent = getInitials(name);
  fallback.hidden = true;

  img.addEventListener("error", () => {
    img.hidden = true;
    fallback.hidden = false;
  });

  wrap.appendChild(img);
  wrap.appendChild(fallback);
  return wrap;
}

export function createBadge(side) {
  const badge = document.createElement("span");
  badge.className = side === "hero" ? "badge badge-hero" : "badge badge-villain";
  badge.textContent = sideLabel(side);
  return badge;
}

export function createViewRankingsButton(slug, side) {
  const link = document.createElement("a");
  link.href = `/characters/${slug}/`;
  link.className = `btn btn-view-rankings btn-view-rankings--${side}`;
  link.textContent = "View Rankings";
  return link;
}

export function renderCharacterCard(character) {
  const card = document.createElement("article");
  card.className = `character-card character-card--${character.side}`;
  card.dataset.slug = character.slug;

  card.appendChild(createCharacterImage(character.name, character.side, character.image_url));

  const body = document.createElement("div");
  body.className = "card-body";

  const title = document.createElement("h3");
  title.className = "card-title";
  title.textContent = character.name;

  const meta = document.createElement("div");
  meta.className = "card-meta";
  meta.appendChild(createBadge(character.side));

  if (character.top_player) {
    const stat = document.createElement("p");
    stat.className = "card-stat";
    stat.innerHTML = `#1 ${formatPlayerNameHtml(character.top_player.nickname, character.top_player.username, character.side, character.top_player.player_slug, nameEffectsFrom(character.top_player))} · ${formatNumber(character.top_player.votes)} votes`;
    body.appendChild(title);
    body.appendChild(meta);
    body.appendChild(stat);
  } else {
    body.appendChild(title);
    body.appendChild(meta);
  }

  const actions = document.createElement("div");
  actions.className = "card-actions";
  actions.appendChild(createViewRankingsButton(character.slug, character.side));
  body.appendChild(actions);

  card.appendChild(body);
  return card;
}
