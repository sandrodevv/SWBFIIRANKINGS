import { initHomePage } from "./pages/home.js";
import { initCharacterPage } from "./pages/character.js";
import { initPlayerPage } from "./pages/player.js";
import { initPfpPage } from "./pages/pfp.js";
import { initDuelistsPage } from "./pages/duelists.js";
import { initSiteNav } from "./nav.js";
import { getSlugFromPath, getPlayerSlugFromPath } from "./utils/format.js";

function init() {
  initSiteNav();

  if (getPlayerSlugFromPath()) {
    initPlayerPage();
  } else if (getSlugFromPath()) {
    initCharacterPage();
  } else if (document.body.classList.contains("page-pfp")) {
    initPfpPage();
  } else if (document.body.classList.contains("page-duelists")) {
    initDuelistsPage();
  } else if (document.body.classList.contains("page-home")) {
    initHomePage();
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
