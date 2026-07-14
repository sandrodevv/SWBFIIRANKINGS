import { getChampions, getRecentVotes } from "../api/client.js";
import { renderChampionCard } from "../render/champion-card.js";
import { renderRecentVotes } from "../render/recent-votes.js";
import { clearElement, showError, showLoading } from "../utils/dom.js";
import { createElement } from "../utils/dom.js";

async function loadChampions() {
  const container = document.querySelector('[data-container="champions"]');
  if (!container) return;

  showLoading(container);

  try {
    const champions = await getChampions();
    clearElement(container);

    if (!champions.length) {
      container.appendChild(createElement("div", "empty-state", "No champions yet."));
      return;
    }

    champions.forEach((champion) => {
      container.appendChild(renderChampionCard(champion));
    });
  } catch (error) {
    showError(container, "Failed to load champions.");
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
  loadChampions();
  loadRecentVotes();
}
