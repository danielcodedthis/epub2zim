// Step 2: choose how to split the book into articles.
// Four choices; the "title list" choice shows an editor with helpers to fill it.

import { api } from "../../api.js";
import { $, $$, el, esc } from "../../dom.js";
import { toast } from "../../components/toast.js";
import { confirmBox } from "../../components/dialog.js";

const CHOICES = [
  ["toc", "📖 Table of contents", "One article per entry in the book's own contents. Best for most EPUBs."],
  ["headings", "🔖 Headings", "A new article at every heading. Good when the contents list is missing or too short."],
  ["files", "🗂️ One per file", "Every chapter file becomes one article. Simple and always works."],
  ["titles", "✍️ Title list", "You list the titles; we find them in the text. For scanned (OCR) books."],
];

const FORMAT_HELP = `Chapter title                  ← a top-level article
- Section inside it            ← one dash per level
= Part One                     ← a group heading on the home page
Title | 12                     ← starts on page file 12
Title | p.204                  ← starts on PRINTED page 204
Title | 12 | Exact words       ← the words that start it in the text
# comment`;

export function renderSplit(ctx, body, head) {
  head.append(el(`<p class="hint">Each article becomes one page in the ZIM file, like one Wikipedia article.</p>`));
  const s = ctx.settings;

  body.append(el(`
    <div>
      <div class="choice-grid" role="group" aria-label="Splitting strategy">
        ${CHOICES.map(([k, t, d]) => `<button type="button" class="choice" data-strategy="${k}" aria-pressed="${s.strategy === k}">
            <b>${t}${ctx.data.inspect.suggested_strategy === k ? ' <span class="chip kw">suggested</span>' : ""}</b><span>${d}</span></button>`).join("")}
      </div>

      <div id="opt-headings" class="field">
        <span>Split at headings down to level <span class="hint">h1 is the biggest heading; level 2 splits at h1 and h2</span></span>
        <select class="select" id="level" style="max-width:220px">
          ${[1, 2, 3, 4].map((n) => `<option value="${n}" ${s.heading_level === n ? "selected" : ""}>h1${n > 1 ? " to h" + n : " only"}</option>`).join("")}
        </select>
      </div>

      <div id="opt-titles">
        <div class="guide lilac"><div>
          <b>How the title list works.</b> Write one title per line, in book order. epub2zim looks for each title in the
          text, starting at the page you give, and starts a new article there. Don't want to type it all?
          Use a helper below to fill it in, then fix what's wrong. Preview (step 4) tells you which titles weren't found.
        </div></div>

        <div class="inline-row" style="margin-top:12px">
          <span class="hint">Fill from:</span>
          <button class="pill-btn" data-suggest="toc">Table of contents</button>
          <button class="pill-btn" data-suggest="headings">Headings</button>
          <button class="pill-btn" data-suggest="running_headers">Running headers (scans)</button>
        </div>
        <div class="inline-row" style="margin-top:8px">
          <span class="hint">or a pattern:</span>
          <input class="input small" id="pattern" placeholder="e.g. ((?:[A-Z]\\w+ ){1,6})Diagnostic Criteria">
          <button class="pill-btn" data-suggest="pattern">Find titles</button>
        </div>

        <label class="field">
          <span>Title list <span class="hint" id="title-count"></span></span>
          <textarea class="textarea mono" id="titles" rows="14" spellcheck="false" placeholder="Garden Basics | 5\n- Soil | 9\nPest Control | 22"></textarea>
        </label>
        <details class="more"><summary>Title list format</summary><pre class="log-view" style="margin-top:8px">${esc(FORMAT_HELP)}</pre></details>

        <fieldset class="group">
          <legend><span class="dot lilac"></span>Scanned-book clean-up</legend>
          <div class="checks">
            <label class="check"><input type="checkbox" id="clean"> Remove page numbers and running headers</label>
            <label class="check"><input type="checkbox" id="lists"> Put “A. … B. …” and “1. … 2. …” items on their own lines</label>
          </div>
          <div class="form-grid" style="margin-top:12px">
            <label class="field"><span>Page offset <span class="hint">“auto”, a number, or empty</span></span>
              <input class="input small" id="offset"></label>
            <label class="field"><span>Paragraph length <span class="hint">characters</span></span>
              <input class="input small" id="para" type="number" min="200" step="50"></label>
          </div>
          <label class="field"><span>Section headings <span class="hint">one phrase per line; each becomes a heading inside articles</span></span>
            <textarea class="textarea mono" id="subs" rows="4" placeholder="Diagnostic Features\nPrevalence\nDifferential Diagnosis"></textarea></label>
          <p class="hint" style="margin-top:8px">Page offset = page file number minus printed page number. “auto” works it out from the page numbers in the text${ctx.data.inspect.page_offset != null ? ` (found: ${ctx.data.inspect.page_offset})` : ""}.</p>
        </fieldset>
      </div>
    </div>`));

  // --- fill in current values ---
  const ta = $(body, "#titles");
  ta.value = ctx.titles;
  $(body, "#clean").checked = s.clean_text;
  $(body, "#lists").checked = s.detect_lists;
  $(body, "#offset").value = s.page_offset;
  $(body, "#para").value = s.paragraph_size;
  $(body, "#subs").value = (s.subheadings || []).join("\n");

  const countTitles = () => {
    const n = ta.value.split("\n").filter((l) => l.trim() && !/^\s*[#=]/.test(l)).length;
    $(body, "#title-count").textContent = n ? `${n} titles` : "empty";
  };
  const showOptions = () => {
    $(body, "#opt-headings").hidden = ctx.settings.strategy !== "headings";
    $(body, "#opt-titles").hidden = ctx.settings.strategy !== "titles";
  };
  countTitles();
  showOptions();

  // --- react to changes ---
  $$(body, "[data-strategy]").forEach((btn) => btn.addEventListener("click", () => {
    ctx.settings.strategy = btn.dataset.strategy;
    $$(body, "[data-strategy]").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    showOptions();
    ctx.changed("settings");
  }));
  $(body, "#level").addEventListener("change", (e) => { ctx.settings.heading_level = Number(e.target.value); ctx.changed("settings"); });
  ta.addEventListener("input", () => { ctx.titles = ta.value; countTitles(); ctx.changed("titles"); });
  $(body, "#clean").addEventListener("change", (e) => { ctx.settings.clean_text = e.target.checked; ctx.changed("settings"); });
  $(body, "#lists").addEventListener("change", (e) => { ctx.settings.detect_lists = e.target.checked; ctx.changed("settings"); });
  $(body, "#offset").addEventListener("input", (e) => { ctx.settings.page_offset = e.target.value.trim(); ctx.changed("settings"); });
  $(body, "#para").addEventListener("change", (e) => { ctx.settings.paragraph_size = Number(e.target.value) || 650; ctx.changed("settings"); });
  $(body, "#subs").addEventListener("input", (e) => {
    ctx.settings.subheadings = e.target.value.split("\n").map((x) => x.trim()).filter(Boolean);
    ctx.changed("settings");
  });

  // --- helpers that fill the title list ---
  $$(body, "[data-suggest]").forEach((btn) => btn.addEventListener("click", async () => {
    const method = btn.dataset.suggest;
    const pattern = $(body, "#pattern").value.trim();
    if (method === "pattern" && !pattern) { toast("Type a pattern first", "err"); return; }
    if (ta.value.trim() && !(await confirmBox({ title: "Replace the title list?",
      text: "The suggestion will replace what is in the title list now.", okLabel: "Replace it", danger: false }))) return;
    btn.disabled = true;
    try {
      const { text } = await api.suggest(ctx.id, method, ctx.settings.heading_level || 2, pattern);
      ta.value = text;
      ctx.titles = text;
      countTitles();
      ctx.changed("titles");
      toast("Title list filled. Check it, then preview (step 4).", "ok");
    } catch (err) { toast(err.message, "err"); }
    btn.disabled = false;
  }));
}
