// home.js: the start page. Explains the idea in four steps, lets you drop an
// EPUB to start, and lists the books you already worked on.

import { api } from "../api.js";
import { $, bytes, el, esc } from "../dom.js";
import { toast } from "../components/toast.js";

const STRATEGY_LABEL = { toc: "table of contents", headings: "headings", files: "one per file", titles: "title list" };

function bookCard(p) {
  return `
    <a class="book-card" href="#/book/${esc(p.id)}">
      <h3>${esc(p.name)}</h3>
      <p class="desc">${esc(p.original_file)}</p>
      <div class="foot">
        <span class="chip len">${esc(STRATEGY_LABEL[p.strategy] || p.strategy)}</span>
        ${p.zim ? `<span class="chip ok">ZIM ready · ${bytes(p.zim_size)}</span>` : '<span class="chip">not built yet</span>'}
        <span class="hint">${esc((p.updated || "").slice(0, 16))}</span>
      </div>
    </a>`;
}

export async function renderHome(view) {
  const projects = await api.projects();
  view.innerHTML = `
    <div class="page">
      <div class="page-head">
        <div class="title">
          <h1>Turn an EPUB into a ZIM file</h1>
          <p class="hint">A ZIM file is an offline mini-wiki: one page per chapter or section, with full-text search.
            Open it in Zimi, Kiwix or any ZIM reader.</p>
        </div>
      </div>

      <div class="how" aria-label="How it works">
        <div class="step-mini"><span class="num-dot">1</span><b>Add a book</b><span class="hint">Drop an .epub file below.</span></div>
        <div class="step-mini"><span class="num-dot">2</span><b>Choose how to split</b><span class="hint">We suggest the best way for your book.</span></div>
        <div class="step-mini"><span class="num-dot">3</span><b>Preview</b><span class="hint">See every article before anything is written.</span></div>
        <div class="step-mini"><span class="num-dot">4</span><b>Build &amp; download</b><span class="hint">Get your .zim file.</span></div>
      </div>

      <section class="section">
        <label class="dropzone" id="drop">
          <span class="flower" aria-hidden="true">✿</span>
          <b>Drop an EPUB file here, or click to choose one</b>
          <span class="hint">It stays on this computer. Nothing is uploaded to the internet.</span>
          <input type="file" accept=".epub,application/epub+zip" hidden id="file">
        </label>
        <p class="hint" id="upload-status" style="margin-top:8px"></p>
      </section>

      <section class="section">
        <div class="section-head"><h2>Your books <span class="count-bubble">${projects.length}</span></h2></div>
        ${projects.length ? `<div class="book-grid">${projects.map(bookCard).join("")}</div>` : `
          <div class="empty">
            <div class="flower" aria-hidden="true">✿</div>
            <h3>No books yet</h3>
            <p>Add your first EPUB above. Not sure which book to try? Any EPUB works: one from your e-book
              library, Project Gutenberg, or one you made with Calibre or Pandoc.</p>
            <div class="actions"><a class="pill-btn" href="#/help">Read the quick guide</a></div>
          </div>`}
      </section>
    </div>`;

  const drop = $(view, "#drop");
  const input = $(view, "#file");
  const status = $(view, "#upload-status");

  async function send(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".epub")) { toast("Please choose an .epub file", "err"); return; }
    status.textContent = `Reading “${file.name}” (${bytes(file.size)})… big books can take a little while.`;
    try {
      const p = await api.upload(file);
      toast("Book added", "ok");
      location.hash = `#/book/${p.id}`;
    } catch (err) {
      status.textContent = "";
      toast(err.message, "err");
    }
  }

  input.addEventListener("change", () => send(input.files[0]));
  ["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", (e) => send(e.dataTransfer.files[0]));
}
