// Step 1: look at the book. Shows what we found, the suggested strategy, and
// lets you read any page file or search for words (useful for scanned books).

import { api } from "../../api.js";
import { $, el, esc } from "../../dom.js";
import { toast } from "../../components/toast.js";

const NAMES = { toc: "Table of contents", headings: "Headings", files: "One article per file", titles: "Title list" };

export function renderLook(ctx, body, head) {
  const i = ctx.data.inspect;
  head.append(el(`<p class="hint">Here is what epub2zim found inside your book.</p>`));
  const headings = Object.entries(i.headings).map(([k, v]) => `${k}: ${v}`).join(" · ") || "none";

  body.append(el(`
    <div>
      <div class="facts">
        <div class="fact"><small>Title</small><b>${esc(i.title || "—")}</b></div>
        <div class="fact"><small>Author</small><b>${esc(i.author || "—")}</b></div>
        <div class="fact"><small>Files</small><b class="num">${i.files}</b></div>
        <div class="fact"><small>Contents entries</small><b class="num">${i.toc_entries}</b></div>
        <div class="fact"><small>Headings</small><b>${esc(headings)}</b></div>
        <div class="fact"><small>Pictures</small><b class="num">${i.images}</b></div>
      </div>
      <div class="guide pink"><div><b>Suggestion: ${esc(NAMES[i.suggested_strategy])}.</b> ${esc(i.reason)}
        ${i.looks_scanned ? "<br>Scanned books need a little more work: step 2 helps you build a title list." : ""}</div></div>
      ${i.toc_preview.length ? `<details class="more"><summary>Show the book's table of contents (first ${i.toc_preview.length})</summary>
        <pre class="log-view" style="margin-top:8px">${esc(i.toc_preview.join("\n"))}</pre></details>` : ""}

      <details class="more" ${i.looks_scanned ? "open" : ""}>
        <summary>Peek inside: read pages and search</summary>
        <p class="hint" style="margin-top:8px">Page numbers here are <b>page files</b>: 1 is the first file of the book.
          In scanned books every printed page is one file${i.page_offset != null ? `, and printed page 1 is file ${1 + i.page_offset}` : ""}.</p>
        <div class="inline-row" style="margin-top:10px">
          <label class="visually-hidden" for="pg">Page file</label>
          <input class="input small tiny" id="pg" type="number" min="1" max="${i.files}" value="1">
          <button class="pill-btn" id="read">Read 3 pages</button>
          <label class="visually-hidden" for="q">Search</label>
          <input class="input small" id="q" placeholder="Find words, e.g. a chapter name">
          <label class="check"><input type="checkbox" id="rx"> regular expression</label>
          <button class="pill-btn" id="find">Find</button>
        </div>
        <div class="reader" id="out"></div>
      </details>
    </div>`));

  const out = $(body, "#out");
  $(body, "#read").addEventListener("click", async () => {
    try {
      const pages = await api.pages(ctx.id, Number($(body, "#pg").value) || 1);
      out.innerHTML = pages.map((p) => `<div class="pg"><b>Page file ${p.page}</b> <span class="hint">(${p.chars} characters)</span><br>${esc(p.text)}</div>`).join("")
        || '<p class="hint">No pages there.</p>';
    } catch (err) { toast(err.message, "err"); }
  });
  const find = async () => {
    const q = $(body, "#q").value.trim();
    if (!q) return;
    try {
      const hits = await api.find(ctx.id, q, $(body, "#rx").checked);
      out.innerHTML = hits.length
        ? `<p class="hint">${hits.length}${hits.length >= 30 ? "+" : ""} matches</p>` + hits.map((h) => `<div class="pg"><b>Page file ${h.page}</b><br>${esc(h.snippet)}</div>`).join("")
        : '<p class="hint">Not found. Scanned text sometimes has typos; try fewer words.</p>';
    } catch (err) { toast(err.message, "err"); }
  };
  $(body, "#find").addEventListener("click", find);
  $(body, "#q").addEventListener("keydown", (e) => { if (e.key === "Enter") find(); });
}
