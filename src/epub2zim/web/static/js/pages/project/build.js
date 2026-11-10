// Step 5: build the .zim file and download it. This holds the page's one
// gradient (primary) button.

import { api } from "../../api.js";
import { $, bytes, el, esc } from "../../dom.js";
import { toast } from "../../components/toast.js";

export function renderBuild(ctx, body, head) {
  head.append(el(`<p class="hint">Makes the file with a full-text search index. Big books can take a minute.</p>`));
  body.append(el(`
    <div>
      <div class="step-actions">
        <button class="primary-btn big" id="build">✿ Build ZIM file</button>
        <span class="hint" id="state"></span>
      </div>
      <div id="result"></div>
      <div id="previous"></div>
    </div>`));

  const result = $(body, "#result");
  const state = $(body, "#state");
  const btn = $(body, "#build");

  const zims = ctx.data.zims || [];
  if (zims.length) {
    $(body, "#previous").innerHTML = `<p class="hint" style="margin-top:14px">Built before: ${zims.map((z) =>
      `<a href="${api.downloadUrl(ctx.id, z.name)}">${esc(z.name)}</a> (${bytes(z.size)})`).join(" · ")}</p>`;
  }

  btn.addEventListener("click", async () => {
    if (!(await ctx.flush())) return;
    btn.disabled = true;
    state.innerHTML = '<span class="status running">building</span>';
    result.innerHTML = "";
    try {
      const r = await api.build(ctx.id);
      state.innerHTML = '<span class="status done">done</span>';
      result.innerHTML = `
        <div class="card result-card" style="margin-top:16px">
          <div class="big-file">
            <span class="icon" aria-hidden="true">✿</span>
            <div style="flex:1;min-width:200px"><h3>${esc(r.file_name)}</h3>
              <p class="hint">${bytes(r.size_bytes)} · ${r.articles} articles · ${r.aliases} aliases · ${r.images} pictures · ${r.seconds}s</p></div>
            <a class="pill-btn active" href="${api.downloadUrl(ctx.id, r.file_name)}" download>⬇ Download</a>
          </div>
          ${r.library_copy ? `<p class="hint">A copy is also in the data folder's <code>output</code> folder, ready for Zimi or kiwix-serve.</p>` : ""}
          ${r.misses.length ? `<div class="form-warn">${r.misses.length} title(s) were not found and are part of the previous article: ${r.misses.map(esc).join(" · ")}</div>` : ""}
          ${r.alias_misses.length ? `<div class="form-warn">Aliases pointing to unknown titles (skipped): ${r.alias_misses.map(esc).join(" · ")}</div>` : ""}
          <div class="guide"><div><b>Open it:</b> in Zimi or Kiwix choose “open file” (or add it to your library folder),
            then use search to jump to any article. On a phone, copy the file over and open it in the Kiwix app.</div></div>
        </div>`;
      toast("Your ZIM file is ready", "ok");
    } catch (err) {
      state.innerHTML = '<span class="status failed">failed</span>';
      toast(err.message, "err");
    }
    btn.disabled = false;
  });
}
