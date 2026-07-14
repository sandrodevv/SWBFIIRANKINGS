import {
  getAllDuelistLeaderboard,
  getDuelistVoteStatus,
  voteForDuelist,
  ApiError,
} from "../api/client.js";
import {
  renderDuelistLeaderboard,
  renderDuelistInlineRankings,
} from "../render/duelist-leaderboard.js";
import { showError, showLoading } from "../utils/dom.js";

const REGION_LABELS = {
  overall: "Display",
  eu: "EU",
  us: "US",
  au: "AU",
};

const PERIOD_LABELS = {
  weekly: "Weekly",
  all_time: "All-time",
};

const REGION_KEYS = ["eu", "us", "au"];

let currentRegion = "overall";
let currentPeriod = "weekly";
let voteStatusByRegion = {
  eu: { can_vote: true },
  us: { can_vote: true },
  au: { can_vote: true },
};

function getListContainer() {
  return document.querySelector('[data-container="duelists"]');
}

function getInlineContainer() {
  return document.querySelector('[data-container="duelist-inline"]');
}

function getVotingRoot() {
  return document.querySelector(".page-duelists .site-main") || document.querySelector(".site-main");
}

function updatePanelLabel() {
  const label = document.querySelector('[data-container="duelist-panel-label"]');
  if (label) {
    label.textContent = `${REGION_LABELS[currentRegion]} · ${PERIOD_LABELS[currentPeriod]} · Top 16`;
  }
}

function updateVoteNote() {
  const note = document.querySelector('[data-container="duelist-vote-note"]');
  if (!note) return;

  if (currentRegion !== "overall" && REGION_KEYS.includes(currentRegion)) {
    const status = voteStatusByRegion[currentRegion];
    if (status?.can_vote === false && status.last_voted_player) {
      note.textContent = `${REGION_LABELS[currentRegion]} voted: ${status.last_voted_player}`;
      return;
    }
    note.textContent = `One vote in ${REGION_LABELS[currentRegion]} per week`;
    return;
  }

  const voted = REGION_KEYS.filter((region) => voteStatusByRegion[region]?.can_vote === false)
    .map((region) => REGION_LABELS[region])
    .join(", ");

  note.textContent = voted
    ? `Voted: ${voted} · one vote per region`
    : "One vote per region per week";
}

function setActiveFilter(attribute, value) {
  document.querySelectorAll(`[${attribute}]`).forEach((button) => {
    button.classList.toggle("is-active", button.getAttribute(attribute) === value);
  });
}

function normalizeVoteStatuses(payload, requestedRegion) {
  if (payload?.regions) {
    voteStatusByRegion = {
      eu: payload.regions.eu || { can_vote: true },
      us: payload.regions.us || { can_vote: true },
      au: payload.regions.au || { can_vote: true },
    };
    return;
  }

  if (requestedRegion && REGION_KEYS.includes(requestedRegion)) {
    voteStatusByRegion = {
      ...voteStatusByRegion,
      [requestedRegion]: payload,
    };
  }
}

function canVoteInRegion(region) {
  return voteStatusByRegion[region]?.can_vote !== false;
}

function applyVoteButtons(root = getVotingRoot()) {
  if (!root) return;
  root.querySelectorAll(".btn-vote").forEach((button) => {
    const row = button.closest("[data-region]");
    const region = row?.dataset.region;
    const enabled = region ? canVoteInRegion(region) : false;
    button.disabled = !enabled;
    button.title = enabled
      ? `Vote in ${REGION_LABELS[region] || region}`
      : `Already voted in ${REGION_LABELS[region] || region} this week`;
  });
}

async function loadVoteStatus() {
  try {
    const requestedRegion = currentRegion === "overall" ? "overall" : currentRegion;
    const status = await getDuelistVoteStatus(requestedRegion);
    normalizeVoteStatuses(status, requestedRegion);
    updateVoteNote();
    applyVoteButtons();
    return status;
  } catch (error) {
    console.error(error);
    return null;
  }
}

async function loadDuelistLeaderboard() {
  const container = getListContainer();
  const inlineContainer = getInlineContainer();
  if (!container || !inlineContainer) return;

  showLoading(container);
  updatePanelLabel();

  try {
    const [entries] = await Promise.all([
      getAllDuelistLeaderboard(currentRegion, currentPeriod),
      loadVoteStatus(),
    ]);
    const options = {
      showVote: true,
      period: currentPeriod,
    };
    renderDuelistLeaderboard(entries, container, options);
    renderDuelistInlineRankings(entries, inlineContainer, options);
    applyVoteButtons();
    updateVoteNote();
  } catch (error) {
    showError(container, "Failed to load duelist rankings.");
    console.error(error);
  }
}

function bindFilters() {
  const filters = document.querySelector('[data-container="duelist-filters"]');
  if (!filters) return;

  filters.addEventListener("click", (event) => {
    const button = event.target.closest(".duelist-filter-btn");
    if (!button) return;

    const region = button.dataset.region;
    const period = button.dataset.period;

    if (region && region !== currentRegion) {
      currentRegion = region;
      setActiveFilter("data-region", region);
      loadDuelistLeaderboard();
    }

    if (period && period !== currentPeriod) {
      currentPeriod = period;
      setActiveFilter("data-period", period);
      loadDuelistLeaderboard();
    }
  });
}

function bindVoting() {
  const root = getVotingRoot();
  if (!root) return;

  root.addEventListener("click", async (event) => {
    const button = event.target.closest(".btn-vote");
    if (!button || button.disabled) return;

    const duelistId = button.dataset.duelistId;
    const row = button.closest("[data-region]");
    const region = row?.dataset.region;
    if (!duelistId || !region) return;

    button.disabled = true;
    const originalText = button.textContent;
    button.textContent = "Voting...";

    try {
      await voteForDuelist(duelistId);
      button.classList.add("voted");
      button.textContent = "Voted!";
      await loadDuelistLeaderboard();
    } catch (error) {
      if (error instanceof ApiError && error.status === 429) {
        button.textContent = "Limit reached";
        if (error.data?.region) {
          voteStatusByRegion[error.data.region] = error.data;
        } else if (region) {
          voteStatusByRegion[region] = { ...error.data, can_vote: false, region };
        }
        applyVoteButtons(root);
        updateVoteNote();
        return;
      }

      button.textContent = "Error";
      console.error("Duelist vote failed:", error);
      setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
      }, 1500);
      return;
    }

    setTimeout(() => {
      button.textContent = originalText;
      button.classList.remove("voted");
    }, 1200);
  });
}

export function initDuelistsPage() {
  bindFilters();
  bindVoting();
  loadDuelistLeaderboard();
}
