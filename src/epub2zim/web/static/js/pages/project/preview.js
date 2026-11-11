// Step 4: preview. Splits the book (nothing is written) and lists the articles,
// with warnings for titles that were not found and suspiciously small/big articles.
// The ✕ on each row leaves that article out (adds it to step 3's list) and previews again.

import { api } from "../../api.js";
import { $, $$, el, esc } from "../../dom.js";
import { toast } from "../../components/toast.js";

const TINY = 150;       // characters: probably a wrong split
const HUGE = 80000;     // characters: maybe split further

export function renderPreview(ctx, body, head) {
  head.append(el(`<p class="hint">See every article before building. Change steps 2–3 and preview again as often as you like.</p>`));
  body.append(el(`
    <div>
      <div class="step-actions">
        <button class="pill-btn active" id="run">✦ Preview articles</button>
        <span class="hint" id="state"></span>
      </div>
      <div id="result"></div>
    </div>`));

  const result = $(body, "#result");
  const state = $(body, "#state");

  const run = async () => {
    if (!(await ctx.flush())) return;
    state.textContent = "Splitting the book…";
    try {
      const pv = await api.preview(ctx.id);
      state.textContent = "";
      result.innerHTML = renderResult(pv);
      bindLeaveOut();
    } catch (err) {
      state.textContent = "";
      toast(err.message, "err");
    }
  };

  // ✕ buttons: leave this article out, then preview again.
  const bindLeaveOut = () => $$(result, "[data-leave]").forEach((btn) => btn.addEventListener("click", async () => {
    const title = btn.dataset.leave;
    ctx.settings.exclude = [...(ctx.settings.exclude || []), title];
    ctx.hooks.refreshExclude?.();
    ctx.changed("settings");
    toast(`“${title}” will be left out (undo in step 3)`, "ok");
    await run();
  }));

  $(body, "#run").addEventListener("click", run);
}

function renderResult(pv) {
  // Short articles that have sub-articles (e.g. "Part One") are fine: they list their chapters.
  const hasChildren = (i) => i + 1 < pv.articles.length && pv.articles[i + 1].level > pv.articles[i].level;
  const isTiny = (a, i) => a.chars < TINY && !hasChildren(i);
  const tiny = pv.articles.filter(isTiny).length;
  const huge = pv.articles.filter((a) => a.chars > HUGE).length;
  const renamed = pv.articles.filter((a) => a.renamed_from).length;

  let html = `<div class="chips" style="margin-top:14px">
      <span class="chip kw">${pv.article_count} articles</span>
      <span class="chip len">${Math.round(pv.total_characters / 1000)}k characters</span>
      ${pv.page_offset != null ? `<span class="chip time">page offset ${pv.page_offset}</span>` : ""}
      ${renamed ? `<span class="chip ok">${renamed} titles improved</span>` : ""}
      ${pv.excluded.length ? `<span class="chip">${pv.excluded.length} left out</span>` : ""}
      ${tiny ? `<span class="chip rep">${tiny} very short</span>` : ""}
      ${huge ? `<span class="chip time">${huge} very long</span>` : ""}
    </div>`;

  if (pv.misses.length) {
    html += `<div class="form-error"><b>${pv.misses.length} title(s) not found:</b> ${pv.misses.map(esc).join(" · ")}
      <br><span style="font-weight:400">Their text stays in the article before them. Fix the spelling to match the book
      (search for it in step 1), add a page number, or add the exact starting words as a third column.</span></div>`;
  }
  pv.warnings.forEach((w) => { html += `<div class="form-warn">${esc(w)}</div>`; });
  if (pv.excluded.length) {
    html += `<p class="hint" style="margin-top:10px">Left out: ${pv.excluded.map(esc).join(" · ")} (change in step 3).</p>`;
  }
  if (!pv.misses.length && pv.article_count) {
    html += `<div class="form-ok">Looks good. Scroll through the list, then build in step 5.</div>`;
  }
  if (!pv.article_count) return html;

  html += `<div class="guide" style="margin-bottom:12px"><div>What to look for: <b>very short</b> articles (often a title found in the wrong place),
    <b>very long</b> ones (a title may be missing), first words that don't match the title, and pages you don't want
    (title page, credits): click ✕ to leave them out.</div></div>
    <div class="table-wrap"><table class="list">
      <thead><tr><th>#</th><th>Title</th><th>Page</th><th>Size</th><th>Starts with</th><th><span class="visually-hidden">Leave out</span></th></tr></thead><tbody>`;
  pv.articles.forEach((a, i) => {
    const cls = isTiny(a, i) ? "tiny" : a.chars > HUGE ? "huge" : "";
    html += `<tr class="${cls}"><td class="num">${a.n}</td>
      <td style="padding-left:${10 + (a.level - 1) * 16}px">${esc(a.title)}
        ${a.renamed_from ? ` <span class="hint">(was “${esc(a.renamed_from)}”)</span>` : ""}
        ${a.group ? ` <span class="chip">${esc(a.group)}</span>` : ""}</td>
      <td class="num">${a.page ?? ""}</td><td class="num size">${a.chars.toLocaleString()}</td>
      <td class="start" title="${esc(a.start)}">${esc(a.start)}</td>
      <td><button class="icon-btn delete" data-leave="${esc(a.title)}" title="Leave “${esc(a.title)}” out" aria-label="Leave ${esc(a.title)} out">✕</button></td></tr>`;
  });
  return html + "</tbody></table></div>";
}
