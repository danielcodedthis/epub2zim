// help.js: a short guide inside the app. The full documentation is in docs/.

const DOCS = "https://github.com/danielcodedthis/epub2zim/blob/main/docs";

export async function renderHelp(view) {
  view.innerHTML = `
    <div class="page narrow">
      <div class="page-head"><div class="title"><h1>Quick guide</h1>
        <p class="hint">Everything you need for your first ZIM file. Longer guides are in the <a href="${DOCS}/README.md" target="_blank" rel="noopener">documentation</a>.</p></div></div>

      <section class="card">
        <h2>What does epub2zim do?</h2>
        <p style="margin-top:8px">It cuts an EPUB book into articles (one per chapter, section or entry) and packs them into a
          <b>ZIM file</b>: the format Wikipedia uses for offline reading. You get a home page with all articles,
          links between them, and full-text search, in Zimi, Kiwix or any ZIM reader.</p>
      </section>

      <section class="card section">
        <h2>Which splitting strategy should I pick?</h2>
        <div class="guide pink"><div><b>Most books → Table of contents.</b> Publisher EPUBs, Calibre, Pandoc, Project Gutenberg. Usually nothing else to do.</div></div>
        <div class="guide"><div><b>Contents list missing or too short → Headings.</b> Try level 2; go to 3 for smaller articles.</div></div>
        <div class="guide lilac"><div><b>Scanned book (one file per printed page) → Title list.</b>
          <ul><li>Use <i>Fill from → Running headers</i> or a pattern to get a first list.</li>
          <li>Preview, look at the “not found” titles, search for them in step 1, fix spelling or add the page.</li>
          <li>Add section phrases (like “Prevalence”) to get headings inside articles.</li></ul></div></div>
        <div class="guide"><div><b>Anything else → One per file.</b> Always works.</div></div>
        <p class="hint" style="margin-top:10px"><a href="${DOCS}/splitting-strategies.md" target="_blank" rel="noopener">More about strategies</a> ·
          <a href="${DOCS}/scanned-books.md" target="_blank" rel="noopener">Scanned books walkthrough</a> ·
          <a href="${DOCS}/title-list-format.md" target="_blank" rel="noopener">Title list format</a></p>
      </section>

      <section class="card section">
        <h2>Where are my files?</h2>
        <p style="margin-top:8px">Everything lives in the data folder (see <a href="#/settings">Settings</a>): one folder per book,
          plus an <code>output</code> folder with every ZIM you built. Download buttons are in step 5 of each book.</p>
      </section>

      <section class="card section">
        <h2>Can an AI assistant do this for me?</h2>
        <p style="margin-top:8px">Yes. epub2zim has an MCP server, so LM Studio, Open WebUI and other MCP clients can inspect, split,
          preview and build books with the same steps. Connection details are on the <a href="#/settings">Settings</a> page;
          ready-made instructions for the assistant are in the project's <code>skills/</code> folder.</p>
      </section>

      <section class="card section">
        <h2>A word on copyright</h2>
        <p style="margin-top:8px">Convert books you have the right to use. A ZIM made from a copyrighted book is for your personal use:
          please don't share it.</p>
      </section>
    </div>`;
}
