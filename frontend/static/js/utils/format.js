export function formatNumber(value) {
  return new Intl.NumberFormat().format(value);
}

export function getSlugFromPath() {
  const match = window.location.pathname.match(/\/characters\/([^/]+)\/?$/);
  return match ? match[1] : null;
}

export function getPlayerSlugFromPath() {
  const match = window.location.pathname.match(/\/players\/([^/]+)\/?$/);
  return match ? match[1] : null;
}

export function getInitials(name) {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function sideLabel(side) {
  return side === "hero" ? "Hero" : "Villain";
}

export function formatRelativeTime(isoString) {
  const date = new Date(isoString);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return "just now";

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;

  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
