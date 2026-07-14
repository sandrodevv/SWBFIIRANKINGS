import { createElement } from "../utils/dom.js";

function hasUsername(username) {
  return typeof username === "string" && username.trim().length > 0;
}

function sideClass(side) {
  if (side === "hero") return "player-name--hero";
  if (side === "villain") return "player-name--villain";
  return "";
}

function normalizeEffects(effects) {
  if (!effects) return { burning: false, smoke: false, glitch: false };
  if (typeof effects === "string") {
    return {
      burning: effects === "burning",
      smoke: effects === "smoke",
      glitch: effects === "glitch",
    };
  }
  return {
    burning: !!effects.burning,
    smoke: !!effects.smoke,
    glitch: !!effects.glitch,
  };
}

export function nameEffectsFrom(obj) {
  if (!obj) return { burning: false, smoke: false, glitch: false };
  return {
    burning: !!(
      obj.name_burning ??
      obj.player_name_burning ??
      obj.last_voted_name_burning
    ),
    smoke: !!(
      obj.name_smoke ??
      obj.player_name_smoke ??
      obj.last_voted_name_smoke
    ),
    glitch: !!(
      obj.name_glitch ??
      obj.player_name_glitch ??
      obj.last_voted_name_glitch
    ),
  };
}

/** @deprecated Prefer nameEffectsFrom */
export function burningEffect(flag) {
  return { burning: !!flag, smoke: false, glitch: false };
}

function effectCharClass({ burning, smoke }) {
  if (burning) return "burn-char";
  if (smoke) return "smoke-char";
  return "effect-char";
}

function appendSmoke(host) {
  const smoke = createElement("span", "name-smoke");
  smoke.setAttribute("aria-hidden", "true");
  for (let i = 0; i < 3; i += 1) {
    const puff = createElement("span", "name-smoke__puff");
    puff.style.setProperty("--p", String(i));
    smoke.appendChild(puff);
  }
  host.appendChild(smoke);
}

function appendEffectChars(host, nickname, charClass) {
  Array.from(nickname).forEach((char, index) => {
    const span = createElement(
      "span",
      charClass,
      char === " " ? "\u00A0" : char
    );
    span.style.setProperty("--i", String(index));
    host.appendChild(span);
  });
}

function createGlitchElement(nickname, playerSlug, { burning, smoke }) {
  const classes = [
    "glitch-name",
    playerSlug ? "player-name__link player-name__link--glitch" : "",
    burning ? "glitch-name--burning" : "",
    smoke ? "glitch-name--smoke" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const el = createElement(playerSlug ? "a" : "span", classes, nickname);
  el.dataset.text = nickname;
  if (playerSlug) el.href = `/players/${playerSlug}/`;
  return el;
}

function createNicknameElement(nickname, playerSlug, effects) {
  const normalized = normalizeEffects(effects);
  const { burning, smoke, glitch } = normalized;
  const hasEffect = burning || smoke || glitch;
  const nickClasses = ["player-name__nickname"];
  if (burning) nickClasses.push("player-name__nickname--burning");
  if (smoke) nickClasses.push("player-name__nickname--smoke");
  if (glitch) nickClasses.push("player-name__nickname--glitch");
  const nickEl = createElement("span", nickClasses.join(" "));

  if (!hasEffect) {
    if (playerSlug) {
      const link = createElement("a", "player-name__link", nickname);
      link.href = `/players/${playerSlug}/`;
      nickEl.appendChild(link);
    } else {
      nickEl.textContent = nickname;
    }
    return nickEl;
  }

  if (smoke) appendSmoke(nickEl);

  if (glitch) {
    nickEl.appendChild(createGlitchElement(nickname, playerSlug, normalized));
    return nickEl;
  }

  const linkClass = [
    "player-name__link",
    burning ? "player-name__link--burning" : "",
    smoke ? "player-name__link--smoke" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const charClass = effectCharClass(normalized);
  if (playerSlug) {
    const link = createElement("a", linkClass);
    link.href = `/players/${playerSlug}/`;
    appendEffectChars(link, nickname, charClass);
    nickEl.appendChild(link);
  } else {
    const core = createElement("span", "name-effect-core");
    appendEffectChars(core, nickname, charClass);
    nickEl.appendChild(core);
  }
  return nickEl;
}

export function renderPlayerName(
  nickname,
  username,
  side = null,
  tag = "span",
  playerSlug = null,
  effects = null
) {
  const normalized = normalizeEffects(effects);
  const classes = ["player-name", sideClass(side)];
  if (normalized.burning) classes.push("player-name--burning");
  if (normalized.smoke) classes.push("player-name--smoke");
  if (normalized.glitch) classes.push("player-name--glitch");
  const wrap = createElement(tag, classes.filter(Boolean).join(" "));
  wrap.appendChild(createNicknameElement(nickname, playerSlug, normalized));

  if (hasUsername(username)) {
    const akaEl = createElement("span", "player-name__aka", "AKA");
    const userEl = createElement("span", "player-name__username", username.trim());
    wrap.append(akaEl, userEl);
  }

  return wrap;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/'/g, "&#39;");
}

function smokeHtml() {
  return (
    '<span class="name-smoke" aria-hidden="true">' +
    '<span class="name-smoke__puff" style="--p:0"></span>' +
    '<span class="name-smoke__puff" style="--p:1"></span>' +
    '<span class="name-smoke__puff" style="--p:2"></span>' +
    "</span>"
  );
}

function glitchNicknameHtml(nickname, playerSlug, { burning, smoke }) {
  const classes = [
    "glitch-name",
    playerSlug ? "player-name__link player-name__link--glitch" : "",
    burning ? "glitch-name--burning" : "",
    smoke ? "glitch-name--smoke" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const text = escapeHtml(nickname);
  const data = escapeAttr(nickname);
  if (playerSlug) {
    return `<a href="/players/${escapeAttr(playerSlug)}/" class="${classes}" data-text="${data}">${text}</a>`;
  }
  return `<span class="${classes}" data-text="${data}">${text}</span>`;
}

function effectNicknameHtml(nickname, playerSlug, effects) {
  const normalized = normalizeEffects(effects);
  const { burning, smoke, glitch } = normalized;
  const prefix = smoke ? smokeHtml() : "";

  if (glitch) {
    return `${prefix}${glitchNicknameHtml(nickname, playerSlug, normalized)}`;
  }

  const charClass = effectCharClass(normalized);
  const chars = Array.from(nickname)
    .map((char, index) => {
      const text = char === " " ? "&nbsp;" : escapeHtml(char);
      return `<span class="${charClass}" style="--i:${index}">${text}</span>`;
    })
    .join("");

  const linkClass = [
    "player-name__link",
    burning ? "player-name__link--burning" : "",
    smoke ? "player-name__link--smoke" : "",
  ]
    .filter(Boolean)
    .join(" ");

  if (playerSlug) {
    return `${prefix}<a href="/players/${escapeHtml(playerSlug)}/" class="${linkClass}">${chars}</a>`;
  }
  return `${prefix}<span class="name-effect-core">${chars}</span>`;
}

export function formatPlayerNameHtml(
  nickname,
  username,
  side = null,
  playerSlug = null,
  effects = null
) {
  const normalized = normalizeEffects(effects);
  const hasEffect = normalized.burning || normalized.smoke || normalized.glitch;
  const modifier = [
    sideClass(side),
    normalized.burning ? "player-name--burning" : "",
    normalized.smoke ? "player-name--smoke" : "",
    normalized.glitch ? "player-name--glitch" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const className = modifier ? `player-name ${modifier}` : "player-name";
  const nickClass = [
    "player-name__nickname",
    normalized.burning ? "player-name__nickname--burning" : "",
    normalized.smoke ? "player-name__nickname--smoke" : "",
    normalized.glitch ? "player-name__nickname--glitch" : "",
  ]
    .filter(Boolean)
    .join(" ");

  let nickContent;
  if (hasEffect) {
    nickContent = effectNicknameHtml(nickname, playerSlug, normalized);
  } else if (playerSlug) {
    nickContent = `<a href="/players/${escapeHtml(playerSlug)}/" class="player-name__link">${escapeHtml(nickname)}</a>`;
  } else {
    nickContent = escapeHtml(nickname);
  }

  if (!hasUsername(username)) {
    return `<span class="${className}"><span class="${nickClass}">${nickContent}</span></span>`;
  }

  const trimmed = escapeHtml(username.trim());
  return `<span class="${className}"><span class="${nickClass}">${nickContent}</span><span class="player-name__aka">AKA</span><span class="player-name__username">${trimmed}</span></span>`;
}
