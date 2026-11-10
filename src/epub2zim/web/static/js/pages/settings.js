// settings.js: where things are stored, how to connect AI assistants (MCP),
// and the theme. Server settings (port, data folder, key) are changed with
// environment variables; this page shows them and gives copy-ready snippets.

import { api } from "../api.js";
import { $, $$, copyText, el, esc } from "../dom.js";
import { toast } from "../components/toast.js";
import { currentTheme, setTheme } from "../components/theme.js";

function snippet(id, title, code, hint = "") {
  return `<div class="field"><span>${title}${hint ? ` <span class="hint">${hint}</span>` : ""}</span>
    <div class="snippet"><pre id="${id}">${esc(code)}</pre><button class="pill-btn copy" data-copy="${id}">Copy</button></div></div>`;
}

export async function renderSettings(view) {
  const c = await api.config();
  const keyPlaceholder = "<your MCP key>";
  const lmStudio = JSON.stringify({ mcpServers: { epub2zim: { url: c.mcp_url, headers: { Authorization: `Bearer ${keyPlaceholder}` } } } }, null, 2);
  const stdio = JSON.stringify({ mcpServers: { epub2zim: { command: "epub2zim", args: ["mcp-stdio", "--data-dir", c.data_dir] } } }, null, 2);
  const dockerUrl = c.mcp_url.replace(/\/\/(localhost|127\.0\.0\.1)/, "//host.docker.internal");

  view.innerHTML = `
    <div class="page narrow">
      <div class="page-head"><div class="title"><h1>Settings</h1>
        <p class="hint">Server settings come from environment variables (see the README). This page shows them and helps you connect AI assistants.</p></div></div>

      <section class="card">
        <h2>Storage</h2>
        <dl class="kv" style="margin-top:12px">
          <dt>Data folder</dt><dd>${esc(c.data_dir)}</dd>
          <dt>Inbox</dt><dd>${esc(c.inbox_dir)}</dd>
          <dt>Finished ZIMs</dt><dd>${esc(c.output_dir)}</dd>
          <dt>Port</dt><dd>${c.port}</dd>
          <dt>Largest upload</dt><dd>${c.max_upload_mb} MB</dd>
          <dt>Version</dt><dd>${esc(c.version)}</dd>
        </dl>
        <div class="guide"><div>Put EPUB files in the <b>inbox</b> folder so AI assistants can import them by name.
          Every finished ZIM is copied to the <b>output</b> folder: point Zimi or kiwix-serve at it.
          Change the folder with <code>EPUB2ZIM_DATA_DIR</code> and the port with <code>EPUB2ZIM_PORT</code>.</div></div>
      </section>

      <section class="card section">
        <h2>AI assistants (MCP)</h2>
        <p class="hint" style="margin-top:4px">Let a local model in LM Studio or Open WebUI convert books for you, using the same steps as this page.</p>
        <dl class="kv" style="margin-top:12px">
          <dt>Server address</dt><dd>${esc(c.mcp_url)}</dd>
          <dt>Key check</dt><dd>${c.mcp_auth ? "on" : '<span style="color:var(--bad)">off (anyone who can reach this port can use it)</span>'}</dd>
          <dt>Key</dt><dd><span id="key">${esc(c.mcp_key_hint)}</span>
            <button class="link-btn" id="show-key">Show</button><button class="link-btn" id="copy-key">Copy</button>
            <span class="hint">(${c.mcp_key_source === "environment" ? "from EPUB2ZIM_MCP_KEY" : "generated, saved in the data folder as mcp_key.txt"})</span></dd>
        </dl>

        <fieldset class="group"><legend><span class="dot pink"></span>LM Studio</legend>
          <p class="hint">LM Studio → Program tab (<code>&gt;_</code>) → Install → Edit <code>mcp.json</code>, paste this, put your key in, save.</p>
          ${snippet("lm", "mcp.json", lmStudio)}
          <details class="more"><summary>LM Studio on another computer, or the stdio way</summary>
            <p class="hint" style="margin-top:8px">Replace <code>localhost</code> with this computer's network address. Or, if epub2zim is installed with pip on the same computer as LM Studio, let LM Studio start it itself (no key needed):</p>
            ${snippet("stdio", "mcp.json (stdio)", stdio)}
          </details>
        </fieldset>

        <fieldset class="group"><legend><span class="dot blue"></span>Open WebUI</legend>
          <p class="hint">Admin Settings → External Tools → <b>+</b> → Type <b>MCP (Streamable HTTP)</b>. Auth: <b>Bearer</b>, Key: your MCP key.</p>
          ${snippet("ow", "Server URL", c.mcp_url)}
          ${snippet("owd", "Server URL when Open WebUI runs in Docker", dockerUrl, "inside a container, localhost means the container itself")}
          <p class="hint" style="margin-top:8px">Then in a chat: <b>+ → Tools → epub2zim</b>, and use a model that supports tool calling.</p>
        </fieldset>
        <p class="hint" style="margin-top:12px">Full guides: <code>docs/lm-studio.md</code>, <code>docs/open-webui.md</code> and the <code>skills/</code> folder in the project.</p>
      </section>

      <section class="card section">
        <h2>Theme</h2>
        <p class="hint" style="margin-top:4px">Saved in this browser only.</p>
        <div class="swatches" style="margin-top:12px">
          <button class="swatch blush" data-theme="blush" aria-pressed="false">Blush</button>
          <button class="swatch midnight" data-theme="midnight" aria-pressed="false">Midnight</button>
        </div>
      </section>
    </div>`;

  // Copy buttons for the snippets.
  $$(view, "[data-copy]").forEach((b) => b.addEventListener("click", async () => {
    await copyText($(view, `#${b.dataset.copy}`).textContent);
    toast("Copied", "ok");
  }));

  // The key is only fetched when you ask for it.
  let key = null;
  const getKey = async () => key || (key = (await api.mcpKey()).key);
  $(view, "#show-key").addEventListener("click", async () => { $(view, "#key").textContent = await getKey(); });
  $(view, "#copy-key").addEventListener("click", async () => { await copyText(await getKey()); toast("Key copied", "ok"); });

  // Theme swatches.
  const mark = () => $$(view, "[data-theme]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.theme === currentTheme())));
  $$(view, "[data-theme]").forEach((b) => b.addEventListener("click", () => { setTheme(b.dataset.theme); mark(); }));
  mark();
}
