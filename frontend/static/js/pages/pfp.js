import { getPfpLeaderboard } from "../api/client.js";
import { renderPfpLeaderboard } from "../render/pfp-leaderboard.js";
import { showError, showLoading } from "../utils/dom.js";

async function loadPfpLeaderboard() {
  const container = document.querySelector('[data-container="pfp"]');
  if (!container) return;

  showLoading(container);

  try {
    const data = await getPfpLeaderboard(1, 15);
    const entries = data.results || data;
    renderPfpLeaderboard(entries, container);
  } catch (error) {
    showError(container, "Failed to load PFP rankings.");
    console.error(error);
  }
}

export function initPfpPage() {
  loadPfpLeaderboard();
}
