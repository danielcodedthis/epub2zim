// project/index.js: one book, as five numbered steps on one page.
//
//   1 look.js     what kind of book is this? peek inside, search
//   2 split.js    how to cut it into articles (+ the title list for scanned books)
//   3 details.js  name, language, aliases, extras
//   4 preview.js  list the articles that would be made
//   5 build.js    make and download the .zim
//
// All steps share one `ctx` object. Changes are saved automatically a moment
// after you stop typing (ctx.changed()), and right before Preview and Build.

import { api } from "../../api.js";
import { $, $$, debounce, el, esc } from "../../dom.js";
import { toast } from "../../components/toast.js";
import { confirmBox } from "../../components/dialog.js";
import { renderLook } from "./look.js";
import { renderSplit } from "./split.js";
import { renderDetails } from "./details.js";
import { renderPreview } from "./preview.js";
import { renderBuild } from "./build.js";

const STEPS = [
  ["look", "Look at the book", renderLook],
  ["split", "Choose how to split", renderSplit],
  ["details", "Name & extras", renderDetails],
  ["preview", "Preview articles", renderPreview],
  ["build", "Build the ZIM", renderBuild],
];

export async function renderProject(view, id) {
  const data = await api.project(id);

  const ctx = {
    id,
    data,                                   // everything the server told us
    settings: { ...data.settings },         // edited in place by the steps
    titles: data.titles || "",
    aliases: data.aliases || "",
    dirty: new Set(),                       // which parts need saving: settings / titles / aliases
    listeners: [],                          // steps can react to changes (e.g. strategy)
    hooks: {},                              // steps can expose refresh functions to each other
    status: null,
  };

  // Save whatever changed. Returns true when everything was saved.
  ctx.flush = async () => {
    try {
      if (ctx.dirty.has("settings")) { ctx.settings = await api.saveSettings(id, ctx.settings); }
      if (ctx.dirty.has("titles")) { await api.saveTitles(id, ctx.titles); }
      if (ctx.dirty.has("aliases")) { await api.saveAliases(id, ctx.aliases); }
      ctx.dirty.clear();
      ctx.status.textContent = "✓ All changes saved";
      return true;
    } catch (err) {
      ctx.status.textContent = "Not saved: " + err.message;
      toast(err.message, "err");
      return false;
    }
  };
  const saveSoon = debounce(ctx.flush, 700);
  ctx.changed = (part) => {
    ctx.dirty.add(part);
    ctx.status.textContent = "Saving…";
    ctx.listeners.forEach((fn) => fn(part));
    saveSoon();
  };
  ctx.onChange = (fn) => ctx.listeners.push(fn);

  const page = el(`
    <div class="page narrow">
      <a class="back-link" href="#/">← Your books</a>
      <div class="page-head">
        <div class="title">
          <h1>${esc(data.summary.name)}</h1>
          <p class="hint">${esc(data.summary.original_file)} · <span id="save-status">✓ All changes saved</span></p>
        </div>
      </div>
      <nav class="steps-nav" aria-label="Steps">
        ${STEPS.map(([key, label], i) => `<a href="javascript:void 0" data-go="${key}"><span class="n">${i + 1}</span>${label}</a>`).join("")}
      </nav>
      <div id="steps"></div>
      <div class="danger-zone"><button class="danger-link" id="delete">Delete this book and its ZIM files…</button></div>
    </div>`);
  ctx.status = $(page, "#save-status");

  const holder = $(page, "#steps");
  STEPS.forEach(([key, label, render], i) => {
    const section = el(`
      <section class="step card" id="step-${key}">
        <div class="step-head"><span class="step-num">${i + 1}</span><div class="text"><h2>${label}</h2></div></div>
        <div class="step-body"></div>
      </section>`);
    holder.append(section);
    render(ctx, $(section, ".step-body"), $(section, ".text"));
  });

  // Step links scroll instead of changing the address (the address picks the page).
  $$(page, "[data-go]").forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById(`step-${a.dataset.go}`).scrollIntoView({ behavior: "smooth", block: "start" });
  }));

  $(page, "#delete").addEventListener("click", async () => {
    const ok = await confirmBox({
      title: "Delete this book?",
      text: `“${data.summary.name}”, its settings, title list and built ZIM files will be removed from the data folder. Copies already in the output folder stay.`,
      okLabel: "Delete book",
    });
    if (!ok) return;
    await api.remove(id);
    toast("Book deleted", "ok");
    location.hash = "#/";
  });

  // Save before leaving the page.
  window.addEventListener("hashchange", () => { if (ctx.dirty.size) ctx.flush(); }, { once: true });

  view.innerHTML = "";
  view.append(page);
}
