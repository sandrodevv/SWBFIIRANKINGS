import { getCharacters, getRecentVotes } from "../api/client.js";
import { renderCharacterCard } from "../render/character-card.js";
import { renderRecentVotes } from "../render/recent-votes.js";
import { clearElement, showError, showLoading } from "../utils/dom.js";
import { createElement } from "../utils/dom.js";

async function getAllCharacters() {
  const pageSize = 50;
  let page = 1;
  let all = [];

  while (true) {
    const data = await getCharacters(page);
    // API may return paginated { results } or a bare list
    const results = data.results || data;
    all = all.concat(results);
    if (!data.next) break;
    page += 1;
    if (page > 20) break;
  }

  return all;
}

async function loadCharacters() {
  const container = document.querySelector('[data-container="champions"]');
  if (!container) return;

  showLoading(container);

  try {
    const characters = await getAllCharacters();
    clearElement(container);

    if (!characters.length) {
      container.appendChild(createElement("div", "empty-state", "No characters yet."));
      return;
    }

    const heroes = characters.filter((c) => c.side === "hero");
    const villains = characters.filter((c) => c.side === "villain");

    [...heroes, ...villains].forEach((character) => {
      container.appendChild(renderCharacterCard(character));
    });
  } catch (error) {
    showError(container, "Failed to load characters.");
    console.error(error);
  }
}

async function loadRecentVotes() {
  const container = document.querySelector('[data-container="recent-votes"]');
  if (!container) return;

  showLoading(container, "Loading...");

  try {
    const votes = await getRecentVotes();
    renderRecentVotes(votes, container);
  } catch (error) {
    showError(container, "Could not load votes.");
    console.error(error);
  }
}

export function initHomePage() {
  loadCharacters();
  loadRecentVotes();
}
