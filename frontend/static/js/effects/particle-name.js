/**
 * Particle-text nickname effect (adapted from CodePen particle write-text).
 * Invisible real-text label reserves normal nickname size; canvas overlays it.
 */

const instances = new Map();
let rafId = 0;
let spawnAcc = 0;
let lastTs = 0;
const SPAWN_EVERY_MS = 28;
const TRAIL_ALPHA = 0.05;
const BG = "#0a0e17";

function createLayer(width, height, dpr) {
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.ceil(width * dpr));
  canvas.height = Math.max(1, Math.ceil(height * dpr));
  const context = canvas.getContext("2d");
  context.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { canvas, context };
}

class Particle {
  constructor(ctx, x, y, w, h) {
    this.ctx = ctx;
    this.x = x;
    this.y = y;
    this.s = 1.2 + Math.random() * 2.2;
    this.a = Math.random() * Math.PI * 2;
    this.w = w;
    this.h = h;
    this.radius = 0.4 + Math.random() * 3.2;
    this.color = this.radius > 1.6 ? "#FF5E4C" : "#ED413C";
  }

  move() {
    this.x += Math.cos(this.a) * this.s;
    this.y += Math.sin(this.a) * this.s;
    this.a += Math.random() * 0.8 - 0.4;

    if (this.x < 0 || this.x > this.w || this.y < 0 || this.y > this.h) {
      return false;
    }

    const ctx = this.ctx;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.closePath();
    return true;
  }
}

function ensureLabel(host, text) {
  let label = host.querySelector(".particle-name__label");
  if (!label) {
    label = document.createElement("span");
    label.className = "particle-name__label";
    label.textContent = text;
    host.textContent = "";
    host.appendChild(label);
  } else if (!label.textContent) {
    label.textContent = text;
  }
  return label;
}

function writeMask(layer, text, font, width, height) {
  const { context } = layer;
  context.clearRect(0, 0, width, height);
  context.font = font;
  context.fillStyle = "#ffffff";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(text, width / 2, height / 2);
}

class ParticleNameInstance {
  constructor(host) {
    this.host = host;
    this.text = (host.dataset.text || host.textContent || "").trim();
    this.particles = [];
    this.visible = true;
    this.disposed = false;

    this.label = ensureLabel(host, this.text);
    host.setAttribute("aria-label", this.text);

    const canvas = document.createElement("canvas");
    canvas.className = "particle-name__canvas";
    canvas.setAttribute("aria-hidden", "true");
    host.appendChild(canvas);
    this.displayCanvas = canvas;

    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.width = 0;
    this.height = 0;

    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(this.label);

    this.intersection = new IntersectionObserver(
      ([entry]) => {
        this.visible = !!entry?.isIntersecting;
      },
      { rootMargin: "40px" }
    );
    this.intersection.observe(host);

    // Layout may not be ready on the same frame the node is inserted
    requestAnimationFrame(() => {
      if (!this.disposed) this.resize();
    });
  }

  resize() {
    if (this.disposed) return;
    const style = getComputedStyle(this.label);
    const font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
    const rect = this.label.getBoundingClientRect();
    const width = Math.max(1, Math.ceil(rect.width));
    const height = Math.max(1, Math.ceil(rect.height));

    if (width === this.width && height === this.height && this.font === font) {
      return;
    }

    this.font = font;
    this.width = width;
    this.height = height;

    this.particleLayer = createLayer(width, height, this.dpr);
    this.maskLayer = createLayer(width, height, this.dpr);
    this.displayLayer = createLayer(width, height, this.dpr);

    writeMask(this.maskLayer, this.text, font, width, height);

    const canvas = this.displayLayer.canvas;
    canvas.className = "particle-name__canvas";
    canvas.setAttribute("aria-hidden", "true");
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    if (this.displayCanvas !== canvas) {
      this.displayCanvas.replaceWith(canvas);
      this.displayCanvas = canvas;
    }

    const clearCtx = this.particleLayer.context;
    clearCtx.fillStyle = BG;
    clearCtx.fillRect(0, 0, width, height);
    this.particles = [];
    this.composite();
  }

  spawn() {
    if (!this.visible || this.disposed || !this.width) return;
    this.particles.push(
      new Particle(
        this.particleLayer.context,
        this.width / 2,
        this.height / 2,
        this.width,
        this.height
      )
    );
  }

  clearTrail() {
    if (!this.particleLayer) return;
    const ctx = this.particleLayer.context;
    ctx.globalAlpha = TRAIL_ALPHA;
    ctx.fillStyle = BG;
    ctx.fillRect(0, 0, this.width, this.height);
    ctx.globalAlpha = 1;
  }

  composite() {
    if (!this.displayLayer || !this.maskLayer || !this.particleLayer) return;
    const out = this.displayLayer.context;
    out.clearRect(0, 0, this.width, this.height);
    out.globalCompositeOperation = "source-over";
    out.drawImage(this.maskLayer.canvas, 0, 0, this.width, this.height);
    out.globalCompositeOperation = "source-in";
    out.drawImage(this.particleLayer.canvas, 0, 0, this.width, this.height);
    out.globalCompositeOperation = "source-over";
  }

  tick() {
    if (this.disposed || !this.visible || !this.particleLayer) return;
    this.clearTrail();
    this.particles = this.particles.filter((p) => p.move());
    this.composite();
  }

  dispose() {
    this.disposed = true;
    this.resizeObserver.disconnect();
    this.intersection.disconnect();
    this.particles = [];
  }
}

function tick(now) {
  rafId = 0;
  if (instances.size === 0) {
    lastTs = 0;
    return;
  }

  const delta = lastTs ? Math.min(now - lastTs, 48) : 16;
  lastTs = now;
  spawnAcc += delta;
  const shouldSpawn = spawnAcc >= SPAWN_EVERY_MS;
  if (shouldSpawn) spawnAcc %= SPAWN_EVERY_MS;

  instances.forEach((inst) => {
    if (shouldSpawn) inst.spawn();
    inst.tick();
  });

  rafId = requestAnimationFrame(tick);
}

function ensureLoop() {
  if (!rafId && instances.size > 0) {
    spawnAcc = SPAWN_EVERY_MS;
    lastTs = 0;
    rafId = requestAnimationFrame(tick);
  }
}

function mount(host) {
  if (!(host instanceof HTMLElement)) return;
  if (instances.has(host)) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    host.classList.add("particle-name--static");
    return;
  }
  const inst = new ParticleNameInstance(host);
  instances.set(host, inst);
  ensureLoop();
}

function unmount(host) {
  const inst = instances.get(host);
  if (!inst) return;
  inst.dispose();
  instances.delete(host);
}

export function initParticleNames(root = document) {
  root.querySelectorAll(".particle-name").forEach(mount);

  if (root.__particleNameObserver) return;
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      mutation.addedNodes.forEach((node) => {
        if (!(node instanceof HTMLElement)) return;
        if (node.matches?.(".particle-name")) mount(node);
        node.querySelectorAll?.(".particle-name").forEach(mount);
      });
      mutation.removedNodes.forEach((node) => {
        if (!(node instanceof HTMLElement)) return;
        if (node.matches?.(".particle-name")) unmount(node);
        node.querySelectorAll?.(".particle-name").forEach(unmount);
      });
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
  root.__particleNameObserver = observer;
}
