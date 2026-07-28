import { formatNumber } from "../utils/format.js";
import { createElement } from "../utils/dom.js";

const RING_RADIUS = 42;
const RING_RADIUS_WEEK = 48;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;
const RING_CIRCUMFERENCE_WEEK = 2 * Math.PI * RING_RADIUS_WEEK;

function safeVotes(value) {
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? n : 0;
}

function deltaLabel(thisWeek, lastWeek) {
  if (lastWeek <= 0 && thisWeek <= 0) return { text: "Even", tone: "flat" };
  if (lastWeek <= 0) return { text: "New activity", tone: "up" };
  const diff = thisWeek - lastWeek;
  const pct = Math.round((diff / lastWeek) * 100);
  if (diff === 0) return { text: "Even with last week", tone: "flat" };
  if (diff > 0) return { text: `+${formatNumber(diff)} (${pct > 0 ? "+" : ""}${pct}%)`, tone: "up" };
  return { text: `${formatNumber(diff)} (${pct}%)`, tone: "down" };
}

function arcLength(value, max, circumference = RING_CIRCUMFERENCE) {
  if (max <= 0) return 0;
  return (Math.min(value, max) / max) * circumference;
}

function createRing({ key, label, total, ranking, duelist, max }) {
  const col = createElement("button", `vote-chart__ring vote-chart__ring--${key}`);
  col.type = "button";
  col.setAttribute("aria-label", `${label}: ${formatNumber(total)} votes`);
  col.dataset.key = key;
  col.dataset.total = String(total);
  col.dataset.ranking = String(ranking);
  col.dataset.duelist = String(duelist);

  const rankingLen = arcLength(ranking, max);
  const duelistLen = arcLength(duelist, max);
  const totalLen = arcLength(total, max, RING_CIRCUMFERENCE_WEEK);

  const visual = createElement("div", "vote-chart__ring-visual");
  visual.innerHTML = `
    <svg class="vote-chart__svg" viewBox="0 0 112 112" aria-hidden="true">
      <circle class="vote-chart__track vote-chart__track--week" cx="56" cy="56" r="${RING_RADIUS_WEEK}"></circle>
      <circle class="vote-chart__track" cx="56" cy="56" r="${RING_RADIUS}"></circle>
      <circle
        class="vote-chart__arc vote-chart__arc--week"
        cx="56" cy="56" r="${RING_RADIUS_WEEK}"
        stroke-dasharray="0 ${RING_CIRCUMFERENCE_WEEK}"
        data-target="${totalLen.toFixed(2)}"
        data-gap="${RING_CIRCUMFERENCE_WEEK}"
      ></circle>
      <circle
        class="vote-chart__arc vote-chart__arc--ranking"
        cx="56" cy="56" r="${RING_RADIUS}"
        stroke-dasharray="0 ${RING_CIRCUMFERENCE}"
        data-target="${rankingLen.toFixed(2)}"
        data-gap="${RING_CIRCUMFERENCE}"
        data-offset="0"
      ></circle>
      <circle
        class="vote-chart__arc vote-chart__arc--duelist"
        cx="56" cy="56" r="${RING_RADIUS}"
        stroke-dasharray="0 ${RING_CIRCUMFERENCE}"
        data-target="${duelistLen.toFixed(2)}"
        data-gap="${RING_CIRCUMFERENCE}"
        data-offset="${(-rankingLen).toFixed(2)}"
      ></circle>
    </svg>
    <div class="vote-chart__ring-center">
      <span class="vote-chart__value">${formatNumber(total)}</span>
      <span class="vote-chart__unit">votes</span>
    </div>
  `;

  const caption = createElement("div", "vote-chart__label", label);
  const split = createElement("div", "vote-chart__split");
  const rankingPct = total > 0 ? (ranking / total) * 100 : 0;
  const duelistPct = total > 0 ? (duelist / total) * 100 : 0;
  split.innerHTML = `
    <div class="vote-chart__split-track" aria-hidden="true">
      <span class="vote-chart__split-fill vote-chart__split-fill--ranking" style="width:${rankingPct}%"></span>
      <span class="vote-chart__split-fill vote-chart__split-fill--duelist" style="width:${duelistPct}%"></span>
    </div>
    <div class="vote-chart__split-meta">
      <span>${formatNumber(ranking)} overall</span>
      <span>${formatNumber(duelist)} duelist</span>
    </div>
  `;

  col.append(visual, caption, split);
  return col;
}

function updateTooltip(tooltip, ring) {
  if (!ring) {
    tooltip.hidden = true;
    tooltip.classList.remove("is-visible");
    return;
  }

  const label = ring.dataset.key === "last" ? "Last week" : "This week";
  const total = Number(ring.dataset.total) || 0;
  const ranking = Number(ring.dataset.ranking) || 0;
  const duelist = Number(ring.dataset.duelist) || 0;

  tooltip.innerHTML = `
    <div class="vote-chart__tooltip-title">${label}</div>
    <div class="vote-chart__tooltip-total">${formatNumber(total)} votes</div>
    <div class="vote-chart__tooltip-rows">
      <div class="vote-chart__tooltip-row">
        <span class="vote-chart__swatch vote-chart__swatch--ranking"></span>
        <span>Overall rankings</span>
        <strong>${formatNumber(ranking)}</strong>
      </div>
      <div class="vote-chart__tooltip-row">
        <span class="vote-chart__swatch vote-chart__swatch--duelist"></span>
        <span>Duelist</span>
        <strong>${formatNumber(duelist)}</strong>
      </div>
    </div>
  `;
  tooltip.hidden = false;
  tooltip.classList.add("is-visible");

  const ringRect = ring.getBoundingClientRect();
  const stage = tooltip.parentElement;
  const stageRect = stage.getBoundingClientRect();
  const tipWidth = tooltip.offsetWidth || 180;
  const left = ringRect.left - stageRect.left + ringRect.width / 2 - tipWidth / 2;
  const top = ringRect.top - stageRect.top - 12;
  tooltip.style.left = `${Math.max(8, Math.min(left, stageRect.width - tipWidth - 8))}px`;
  tooltip.style.top = `${Math.max(8, top - tooltip.offsetHeight)}px`;
}

function bindInteractivity(root, rings, tooltip) {
  let active = null;

  const setActive = (ring) => {
    rings.forEach((r) => r.classList.toggle("is-active", r === ring));
    active = ring;
    updateTooltip(tooltip, ring);
  };

  rings.forEach((ring) => {
    ring.addEventListener("mouseenter", () => setActive(ring));
    ring.addEventListener("focus", () => setActive(ring));
    ring.addEventListener("click", () => setActive(ring === active ? null : ring));
    ring.addEventListener("blur", () => {
      window.requestAnimationFrame(() => {
        if (!root.contains(document.activeElement)) setActive(null);
      });
    });
  });

  root.addEventListener("mouseleave", () => {
    if (document.activeElement && root.contains(document.activeElement)) return;
    setActive(null);
  });
}

function animateRings(root) {
  const arcs = root.querySelectorAll(".vote-chart__arc");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const reveal = () => {
    arcs.forEach((arc, index) => {
      const target = Number(arc.dataset.target) || 0;
      const gap = Number(arc.dataset.gap) || RING_CIRCUMFERENCE;
      const offset = Number(arc.dataset.offset) || 0;
      const apply = () => {
        arc.style.strokeDasharray = `${target} ${gap}`;
        arc.style.strokeDashoffset = String(offset);
        arc.classList.add("is-drawn");
      };
      if (reduceMotion) {
        apply();
        return;
      }
      window.setTimeout(apply, 100 + index * 70);
    });
  };

  if (!("IntersectionObserver" in window)) {
    reveal();
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        reveal();
        observer.disconnect();
      });
    },
    { threshold: 0.3 }
  );
  observer.observe(root);
}

const SIDE_MIN_WIDTH = 1400;
const SIDE_GAP = 24;
const SIDE_CHART_WIDTH = 280;

/**
 * @param {HTMLElement} shell
 */
export function bindVoteChartPlacement(shell) {
  if (!shell) return () => {};

  const update = () => {
    const viewportWide = window.innerWidth >= SIDE_MIN_WIDTH;
    let hasSideRoom = viewportWide;

    if (viewportWide) {
      const column = document.querySelector(
        "#player-assignments .container, #player-header .container"
      );
      if (column) {
        const columnRight = column.getBoundingClientRect().right;
        const freeRight = window.innerWidth - columnRight;
        hasSideRoom = freeRight >= SIDE_CHART_WIDTH + SIDE_GAP;
      }
    }

    shell.classList.toggle("is-side", hasSideRoom);
    shell.classList.toggle("is-bottom", !hasSideRoom);
  };

  update();
  window.addEventListener("resize", update);
  return update;
}

/**
 * @param {HTMLElement} container
 * @param {object} player
 */
export function renderVoteChart(container, player) {
  const lastWeek = safeVotes(player.last_week_votes);
  const thisWeek = safeVotes(player.weekly_votes);
  const rankingLast = safeVotes(player.ranking_last_week_votes);
  const rankingThis = safeVotes(player.ranking_weekly_votes);
  const duelistLast = safeVotes(player.duelist_last_week_votes);
  const duelistThis = safeVotes(player.duelist_weekly_votes);
  const max = Math.max(lastWeek, thisWeek, 1);
  const delta = deltaLabel(thisWeek, lastWeek);

  const root = createElement("div", "vote-chart");
  const stage = createElement("div", "vote-chart__stage");

  const lastRing = createRing({
    key: "last",
    label: "Last week",
    total: lastWeek,
    ranking: rankingLast,
    duelist: duelistLast,
    max,
  });
  const thisRing = createRing({
    key: "this",
    label: "This week",
    total: thisWeek,
    ranking: rankingThis,
    duelist: duelistThis,
    max,
  });

  const grid = createElement("div", "vote-chart__grid");
  grid.append(lastRing, thisRing);
  stage.appendChild(grid);

  const tooltip = createElement("div", "vote-chart__tooltip");
  tooltip.hidden = true;
  tooltip.setAttribute("role", "status");
  stage.appendChild(tooltip);

  const meta = createElement("div", "vote-chart__meta");
  const deltaEl = createElement("div", `vote-chart__delta vote-chart__delta--${delta.tone}`);
  deltaEl.textContent = delta.text;

  const legend = createElement("div", "vote-chart__legend");
  legend.innerHTML = `
    <span class="vote-chart__legend-item">
      <span class="vote-chart__swatch vote-chart__swatch--ranking"></span>
      Overall rankings
    </span>
    <span class="vote-chart__legend-item">
      <span class="vote-chart__swatch vote-chart__swatch--duelist"></span>
      Duelist
    </span>
  `;
  meta.append(deltaEl, legend);

  root.append(stage, meta);
  container.appendChild(root);

  bindInteractivity(root, [lastRing, thisRing], tooltip);
  animateRings(root);
  return root;
}
