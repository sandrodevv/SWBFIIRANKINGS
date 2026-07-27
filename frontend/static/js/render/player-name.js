import { createElement } from "../utils/dom.js";

function hasUsername(username) {
  return typeof username === "string" && username.trim().length > 0;
}

function sideClass(side) {
  if (side === "hero") return "player-name--hero";
  if (side === "villain") return "player-name--villain";
  return "";
}

function emptyEffects() {
  return {
    burning: false,
    smoke: false,
    glitch: false,
    corrupt: false,
    beskar: false,
    particles: false,
    crack: false,
  };
}

function normalizeEffects(effects) {
  if (!effects) return emptyEffects();
  if (typeof effects === "string") {
    return {
      burning: effects === "burning",
      smoke: effects === "smoke",
      glitch: effects === "glitch",
      corrupt: effects === "corrupt",
      beskar: effects === "beskar",
      particles: effects === "particles",
      crack: effects === "crack",
    };
  }
  return {
    burning: !!effects.burning,
    smoke: !!effects.smoke,
    glitch: !!effects.glitch,
    corrupt: !!effects.corrupt,
    beskar: !!effects.beskar,
    particles: !!effects.particles,
    crack: !!effects.crack,
  };
}

export function nameEffectsFrom(obj) {
  if (!obj) return emptyEffects();
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
    corrupt: !!(
      obj.name_corrupt ??
      obj.player_name_corrupt ??
      obj.last_voted_name_corrupt
    ),
    beskar: !!(
      obj.name_beskar ??
      obj.player_name_beskar ??
      obj.last_voted_name_beskar
    ),
    particles: !!(
      obj.name_particles ??
      obj.player_name_particles ??
      obj.last_voted_name_particles
    ),
    crack: !!(
      obj.name_crack ??
      obj.player_name_crack ??
      obj.last_voted_name_crack
    ),
  };
}

/** @deprecated Prefer nameEffectsFrom */
export function burningEffect(flag) {
  return { ...emptyEffects(), burning: !!flag };
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

function createCorruptElement(nickname, playerSlug, { burning, smoke }) {
  const classes = [
    "corrupt-name",
    playerSlug ? "player-name__link player-name__link--corrupt" : "",
    burning ? "corrupt-name--burning" : "",
    smoke ? "corrupt-name--smoke" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const el = createElement(playerSlug ? "a" : "span", classes, nickname);
  el.dataset.text = nickname;
  if (playerSlug) el.href = `/players/${playerSlug}/`;
  return el;
}

function createBeskarElement(nickname, playerSlug) {
  const classes = [
    "beskar-text",
    playerSlug ? "player-name__link player-name__link--beskar" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const el = createElement(playerSlug ? "a" : "span", classes, nickname);
  if (playerSlug) el.href = `/players/${playerSlug}/`;
  return el;
}

function createParticlesElement(nickname, playerSlug) {
  const classes = [
    "particle-name",
    playerSlug ? "player-name__link player-name__link--particles" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const el = createElement(playerSlug ? "a" : "span", classes, nickname);
  el.dataset.text = nickname;
  if (playerSlug) el.href = `/players/${playerSlug}/`;
  return el;
}

function createCrackElement(nickname, playerSlug) {
  const classes = [
    "crack-name",
    playerSlug ? "player-name__link player-name__link--crack" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const el = createElement(playerSlug ? "a" : "span", classes);
  el.dataset.text = nickname;
  el.appendChild(document.createTextNode(nickname));
  const mid = createElement("span", "crack-name__mid", nickname);
  mid.setAttribute("aria-hidden", "true");
  el.appendChild(mid);
  if (playerSlug) el.href = `/players/${playerSlug}/`;
  return el;
}

function createNicknameElement(nickname, playerSlug, effects) {
  const normalized = normalizeEffects(effects);
  const { burning, smoke, glitch, corrupt, beskar, particles, crack } =
    normalized;
  const hasEffect =
    burning || smoke || glitch || corrupt || beskar || particles || crack;
  const nickClasses = ["player-name__nickname"];
  if (burning) nickClasses.push("player-name__nickname--burning");
  if (smoke) nickClasses.push("player-name__nickname--smoke");
  if (glitch) nickClasses.push("player-name__nickname--glitch");
  if (corrupt) nickClasses.push("player-name__nickname--corrupt");
  if (beskar) nickClasses.push("player-name__nickname--beskar");
  if (particles) nickClasses.push("player-name__nickname--particles");
  if (crack) nickClasses.push("player-name__nickname--crack");
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

  if (corrupt) {
    nickEl.appendChild(createCorruptElement(nickname, playerSlug, normalized));
    return nickEl;
  }

  if (beskar) {
    nickEl.appendChild(createBeskarElement(nickname, playerSlug));
    return nickEl;
  }

  if (particles) {
    nickEl.appendChild(createParticlesElement(nickname, playerSlug));
    return nickEl;
  }

  if (crack) {
    nickEl.appendChild(createCrackElement(nickname, playerSlug));
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
  if (normalized.corrupt) classes.push("player-name--corrupt");
  if (normalized.beskar) classes.push("player-name--beskar");
  if (normalized.particles) classes.push("player-name--particles");
  if (normalized.crack) classes.push("player-name--crack");
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

function corruptNicknameHtml(nickname, playerSlug, { burning, smoke }) {
  const classes = [
    "corrupt-name",
    playerSlug ? "player-name__link player-name__link--corrupt" : "",
    burning ? "corrupt-name--burning" : "",
    smoke ? "corrupt-name--smoke" : "",
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

function beskarNicknameHtml(nickname, playerSlug) {
  const classes = [
    "beskar-text",
    playerSlug ? "player-name__link player-name__link--beskar" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const text = escapeHtml(nickname);
  if (playerSlug) {
    return `<a href="/players/${escapeAttr(playerSlug)}/" class="${classes}">${text}</a>`;
  }
  return `<span class="${classes}">${text}</span>`;
}

function particlesNicknameHtml(nickname, playerSlug) {
  const classes = [
    "particle-name",
    playerSlug ? "player-name__link player-name__link--particles" : "",
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

function crackNicknameHtml(nickname, playerSlug) {
  const classes = [
    "crack-name",
    playerSlug ? "player-name__link player-name__link--crack" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const text = escapeHtml(nickname);
  const data = escapeAttr(nickname);
  const mid = `<span class="crack-name__mid" aria-hidden="true">${text}</span>`;
  if (playerSlug) {
    return `<a href="/players/${escapeAttr(playerSlug)}/" class="${classes}" data-text="${data}">${text}${mid}</a>`;
  }
  return `<span class="${classes}" data-text="${data}">${text}${mid}</span>`;
}

function effectNicknameHtml(nickname, playerSlug, effects) {
  const normalized = normalizeEffects(effects);
  const { burning, smoke, glitch, corrupt, beskar, particles, crack } =
    normalized;
  const prefix = smoke ? smokeHtml() : "";

  if (glitch) {
    return `${prefix}${glitchNicknameHtml(nickname, playerSlug, normalized)}`;
  }

  if (corrupt) {
    return `${prefix}${corruptNicknameHtml(nickname, playerSlug, normalized)}`;
  }

  if (beskar) {
    return `${prefix}${beskarNicknameHtml(nickname, playerSlug)}`;
  }

  if (particles) {
    return `${prefix}${particlesNicknameHtml(nickname, playerSlug)}`;
  }

  if (crack) {
    return `${prefix}${crackNicknameHtml(nickname, playerSlug)}`;
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
  const hasEffect =
    normalized.burning ||
    normalized.smoke ||
    normalized.glitch ||
    normalized.corrupt ||
    normalized.beskar ||
    normalized.particles ||
    normalized.crack;
  const modifier = [
    sideClass(side),
    normalized.burning ? "player-name--burning" : "",
    normalized.smoke ? "player-name--smoke" : "",
    normalized.glitch ? "player-name--glitch" : "",
    normalized.corrupt ? "player-name--corrupt" : "",
    normalized.beskar ? "player-name--beskar" : "",
    normalized.particles ? "player-name--particles" : "",
    normalized.crack ? "player-name--crack" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const className = modifier ? `player-name ${modifier}` : "player-name";
  const nickClass = [
    "player-name__nickname",
    normalized.burning ? "player-name__nickname--burning" : "",
    normalized.smoke ? "player-name__nickname--smoke" : "",
    normalized.glitch ? "player-name__nickname--glitch" : "",
    normalized.corrupt ? "player-name__nickname--corrupt" : "",
    normalized.beskar ? "player-name__nickname--beskar" : "",
    normalized.particles ? "player-name__nickname--particles" : "",
    normalized.crack ? "player-name__nickname--crack" : "",
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
