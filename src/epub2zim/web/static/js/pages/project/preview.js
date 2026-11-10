// Step 4: preview. Splits the book (nothing is written) and lists the articles,
// with warnings for titles that were not found and suspiciously small/big articles.

import { api } from "../../api.js";
import { $, el, esc } from "../../dom.js";
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

  $(body, "#run").addEventListener("click", async () => {
    if (!(await ctx.flush())) return;
    state.textContent = "Splitting the book…";
    result.innerHTML = "";
    try {
      const pv = await api.preview(ctx.id);
      state.textContent = "";
      result.innerHTML = renderResult(pv);
    } catch (err) {
      state.textContent = "";
      toast(err.message, "err");
    }
  });
}

function renderResult(pv) {
  const tiny = pv.articles.filter((a) => a.chars < TINY).length;
  const huge = pv.articles.filter((a) => a.chars > HUGE).length;
  let html = `<div class="chips" style="margin-top:14px">
      <span class="chip kw">${pv.article_count} articles</span>
      <span class="chip len">${Math.round(pv.total_characters / 1000)}k characters</span>
      ${pv.page_offset != null ? `<span class="chip time">page offset ${pv.page_offset}</span>` : ""}
      ${tiny ? `<span class="chip rep">${tiny} very short</span>` : ""}
      ${huge ? `<span class="chip time">${huge} very long</span>` : ""}
    </div>`;

  if (pv.misses.length) {
    html += `<div class="form-error"><b>${pv.misses.length} title(s) not found:</b> ${pv.misses.map(esc).join(" · ")}
      <br><span style="font-weight:400">Their text stays in the article before them. Fix the spelling to match the book
      (search for it in step 1), add a page number, or add the exact starting words as a third column.</span></div>`;
  }
  pv.warnings.forEach((w) => { html += `<div class="form-warn">${esc(w)}</div>`; });
  if (!pv.misses.length && pv.article_count) {
    html += `<div class="form-ok">Looks good. Scroll through the list, then build in step 5.</div>`;
  }
  if (!pv.article_count) return html;

  html += `<div class="guide" style="margin-bottom:12px"><div>What to look for: <b>very short</b> articles (often a title found in the wrong place),
    <b>very long</b> ones (a title may be missing), and first words that don't match the title.</div></div>
    <div class="table-wrap"><table class="list">
      <thead><tr><th>#</th><th>Title</th><th>Page</th><th>Size</th><th>Starts with</th></tr></thead><tbody>`;
  for (const a of pv.articles) {
    const cls = a.chars < TINY ? "tiny" : a.chars > HUGE ? "huge" : "";
    html += `<tr class="${cls}"><td class="num">${a.n}</td>
      <td style="padding-left:${10 + (a.level - 1) * 16}px">${esc(a.title)}${a.group ? ` <span class="chip">${esc(a.group)}</span>` : ""}</td>
      <td class="num">${a.page ?? ""}</td><td class="num size">${a.chars.toLocaleString()}</td>
      <td class="start" title="${esc(a.start)}">${esc(a.start)}</td></tr>`;
  }
  return html + "</tbody></table></div>";
}
