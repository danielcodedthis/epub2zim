// app.js: the little router. The part of the address after "#" picks the page:
//   #/             your books (home.js)
//   #/book/<id>    one book, step by step (project/index.js)
//   #/help         quick guide (help.js)
//   #/settings     connection details, MCP, theme (settings.js)

import { renderHome } from "./pages/home.js";
import { renderProject } from "./pages/project/index.js";
import { renderHelp } from "./pages/help.js";
import { renderSettings } from "./pages/settings.js";
import { esc } from "./dom.js";

const view = document.getElementById("view");

function markNav(name) {
  document.querySelectorAll("[data-nav]").forEach((a) => {
    if (a.dataset.nav === name) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
}

async function route() {
  const hash = location.hash.replace(/^#/, "") || "/";
  const parts = hash.split("/").filter(Boolean);
  view.innerHTML = '<div class="loading">Loading…</div>';
  try {
    if (parts[0] === "book" && parts[1]) { markNav("home"); await renderProject(view, parts[1]); }
    else if (parts[0] === "help") { markNav("help"); await renderHelp(view); }
    else if (parts[0] === "settings") { markNav("settings"); await renderSettings(view); }
    else { markNav("home"); await renderHome(view); }
  } catch (err) {
    view.innerHTML = `<div class="page narrow"><div class="empty"><div class="flower">✿</div>
      <h2>Something went wrong</h2><p>${esc(err.message)}</p>
      <div class="actions"><a class="pill-btn" href="#/">Back to your books</a></div></div></div>`;
  }
  if (!location.hash.includes("step-")) window.scrollTo(0, 0);
  view.focus({ preventScroll: true });
}

window.addEventListener("hashchange", route);
route();
