const API_BASE = "/api";

function getCsrfToken() {
  const input = document.querySelector("[name=csrfmiddlewaretoken]");
  if (input) return input.value;
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (options.method && options.method !== "GET") {
    headers["X-CSRFToken"] = getCsrfToken();
  }

  const response = await fetch(`${API_BASE}${path}`, {
    headers,
    credentials: "same-origin",
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    let data = null;
    try {
      data = await response.json();
      message = data.detail || data.message || JSON.stringify(data);
    } catch {
      // use default message
    }
    throw new ApiError(message, response.status, data);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function getCharacters(page = 1) {
  return request(`/characters/?page=${page}&page_size=50`);
}

export function getCharacter(slug) {
  return request(`/characters/${slug}/`);
}

export function getCharacterRankings(slug, page = 1, pageSize = 10) {
  return request(`/characters/${slug}/rankings/?page=${page}&page_size=${pageSize}`);
}

export async function getAllCharacterRankings(slug) {
  const pageSize = 50;
  let page = 1;
  let allRankings = [];

  while (true) {
    const data = await getCharacterRankings(slug, page, pageSize);
    const results = data.results || data;
    allRankings = allRankings.concat(results);
    if (!data.next) break;
    page += 1;
  }

  return allRankings;
}

export function getVoteStatus(slug) {
  return request(`/characters/${slug}/vote-status/`);
}

export function getPfpLeaderboard(page = 1, pageSize = 50) {
  return request(`/pfp/?page=${page}&page_size=${pageSize}`);
}

export function getDuelistLeaderboard(region = "overall", period = "weekly", page = 1, pageSize = 50) {
  const params = new URLSearchParams({
    region,
    period,
    page: String(page),
    page_size: String(pageSize),
  });
  return request(`/duelists/?${params.toString()}`);
}

export async function getAllDuelistLeaderboard(region = "overall", period = "weekly") {
  const pageSize = 100;
  let page = 1;
  let allEntries = [];

  while (true) {
    const data = await getDuelistLeaderboard(region, period, page, pageSize);
    const results = data.results || data;
    allEntries = allEntries.concat(results);
    if (!data.next) break;
    page += 1;
  }

  return allEntries;
}

export function getDuelistVoteStatus(region = "overall") {
  const params = new URLSearchParams({ region });
  return request(`/duelists/vote-status/?${params.toString()}`);
}

export function voteForDuelist(duelistId) {
  return request(`/duelists/${duelistId}/vote/`, { method: "POST" });
}

export function getRecentVotes() {
  return request("/recent-votes/");
}

export function getChampions() {
  return request("/champions/");
}

export function getPlayer(slug) {
  return request(`/players/${slug}/`);
}

export function voteForRanking(rankingId) {
  return request(`/rankings/${rankingId}/vote/`, { method: "POST" });
}
