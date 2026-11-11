// Step 3: name the ZIM file, choose a cover, tidy article titles, leave articles
// out, and extras (links, pictures, aliases).

import { api } from "../../api.js";
import { $, $$, el } from "../../dom.js";
import { toast } from "../../components/toast.js";
import { confirmBox } from "../../components/dialog.js";

const PREFIX = [
  ["never", "Never"],
  ["short", "Short titles only"],
  ["always", "Always"],
];

export function renderDetails(ctx, body, head) {
  head.append(el(`<p class="hint">What your ZIM reader shows in its library, plus article titles and what to leave out.</p>`));
  const s = ctx.settings;

  body.append(el(`
    <div>
      <fieldset class="group">
        <legend><span class="dot pink"></span>About the file</legend>
        <div class="cover-row">
          <div class="cover-box" id="cover-box"><img id="cover-img" alt="Cover"><span id="cover-none" class="hint">No cover</span></div>
          <div class="cover-text">
            <b>Cover</b>
            <p class="hint">Used as the library icon and at the top of the ZIM's home page.
              The book's own cover is used unless you upload one. A square picture around 500×500 works best.</p>
            <div class="inline-row" style="margin-top:8px">
              <label class="pill-btn" for="cover-file">Upload a cover…</label>
              <input type="file" id="cover-file" accept="image/png,image/jpeg,image/webp,image/gif" hidden>
              <button class="link-btn" id="cover-remove" hidden>Remove my cover</button>
            </div>
          </div>
        </div>
        <div class="form-grid" style="margin-top:14px">
          <label class="field"><span>Title</span><input class="input" id="title" maxlength="200"></label>
          <label class="field"><span>Author</span><input class="input" id="creator"></label>
          <label class="field"><span>Language <span class="hint">3 letters: eng, deu, fra, bul…</span></span><input class="input" id="language" maxlength="3"></label>
        </div>
        <label class="field"><span>Short description <span class="hint" id="desc-count"></span></span>
          <input class="input" id="description" maxlength="80" placeholder="One line about the book, e.g. “Dostoevsky's novel, Bulgarian translation”"></label>
        <p class="form-warn" id="desc-warn" style="margin-top:8px">Recommended: readers show this line in their library. Without it, a generic text is used.</p>
        <details class="more"><summary>More file details</summary>
          <div class="form-grid" style="margin-top:10px">
            <label class="field"><span>Publisher</span><input class="input" id="publisher"></label>
            <label class="field"><span>Short name <span class="hint">letters, numbers, _</span></span><input class="input" id="name" placeholder="made from the title"></label>
          </div>
        </details>
      </fieldset>

      <fieldset class="group">
        <legend><span class="dot mint"></span>Article titles</legend>
        <div class="field">
          <span>Put the part's name in front of a chapter title</span>
          <div class="segmented" role="group" aria-label="Parent prefix">
            ${PREFIX.map(([k, label]) => `<button type="button" data-prefix="${k}" aria-pressed="${s.parent_prefix === k}">${label}</button>`).join("")}
          </div>
          <p class="hint">For chapters called only “I”, “II”, “3” or “Chapter 4”: “Part One · I” is much easier to find than ten articles called “I”.
            <i>Short titles only</i> changes just those; <i>Always</i> changes every sub-article.</p>
        </div>
        <label class="field"><span>Rename articles <span class="hint">one per line: Old title = New title</span></span>
          <textarea class="textarea mono" id="renames" rows="3" spellcheck="false" placeholder="Част първа · I = Част първа · I. Горещ юли"></textarea></label>
        <label class="field"><span>Leave out these articles <span class="hint">one title per line; * matches anything; upper/lower case doesn't matter</span></span>
          <textarea class="textarea mono" id="exclude" rows="3" spellcheck="false" placeholder="Title page\nCredits\nAbout this edition*"></textarea></label>
        <p class="hint" style="margin-top:6px">Tip: in step 4 each article has a ✕ button that adds it here.</p>
      </fieldset>

      <fieldset class="group">
        <legend><span class="dot blue"></span>Extras</legend>
        <div class="checks">
          <label class="check"><input type="checkbox" id="autolink"> Link mentions of other article titles (like a wiki)</label>
          <label class="check"><input type="checkbox" id="images"> Include the book's pictures</label>
          <label class="check"><input type="checkbox" id="coverhome"> Show the cover on the home page</label>
        </div>
        <label class="field" style="max-width:260px"><span>Shortest title to link <span class="hint">characters</span></span>
          <input class="input small" id="minlen" type="number" min="3" max="60"></label>
      </fieldset>

      <fieldset class="group">
        <legend><span class="dot lilac"></span>Aliases (extra search names)</legend>
        <p class="hint">Typing an alias in your reader's search opens the article. One per line:
          <code>Short name = Article title</code>. Great for abbreviations and other spellings.</p>
        <textarea class="textarea mono" id="aliases" rows="5" spellcheck="false" placeholder="PTSD = Posttraumatic Stress Disorder\nThe Whale = Moby-Dick"></textarea>
      </fieldset>
    </div>`));

  // --- simple text fields ---
  const bindText = (id, key) => {
    const input = $(body, `#${id}`);
    input.value = s[key] ?? "";
    input.addEventListener("input", () => { ctx.settings[key] = input.value; ctx.changed("settings"); });
    return input;
  };
  bindText("title", "title");
  bindText("creator", "creator");
  bindText("language", "language");
  bindText("publisher", "publisher");
  bindText("name", "name");
  const desc = bindText("description", "description");
  const countDesc = () => {
    $(body, "#desc-count").textContent = `${desc.value.length}/80`;
    $(body, "#desc-warn").hidden = desc.value.trim().length > 0;
  };
  desc.addEventListener("input", countDesc);
  countDesc();

  // --- lists edited as one-per-line text ---
  const bindLines = (id, key) => {
    const ta = $(body, `#${id}`);
    const fill = () => { ta.value = (ctx.settings[key] || []).join("\n"); };
    fill();
    ta.addEventListener("input", () => {
      ctx.settings[key] = ta.value.split("\n").map((x) => x.trim()).filter(Boolean);
      ctx.changed("settings");
    });
    return fill;
  };
  bindLines("renames", "renames");
  ctx.hooks.refreshExclude = bindLines("exclude", "exclude");   // step 4's ✕ buttons call this

  $$(body, "[data-prefix]").forEach((b) => b.addEventListener("click", () => {
    ctx.settings.parent_prefix = b.dataset.prefix;
    $$(body, "[data-prefix]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    ctx.changed("settings");
  }));

  // --- checkboxes ---
  const bindCheck = (id, key) => {
    const box = $(body, `#${id}`);
    box.checked = s[key];
    box.addEventListener("change", () => { ctx.settings[key] = box.checked; ctx.changed("settings"); });
  };
  bindCheck("autolink", "autolink");
  bindCheck("images", "include_images");
  bindCheck("coverhome", "cover_on_home");
  const minlen = $(body, "#minlen");
  minlen.value = s.autolink_min_length;
  minlen.addEventListener("change", () => { ctx.settings.autolink_min_length = Number(minlen.value) || 8; ctx.changed("settings"); });

  const aliases = $(body, "#aliases");
  aliases.value = ctx.aliases;
  aliases.addEventListener("input", () => { ctx.aliases = aliases.value; ctx.changed("aliases"); });

  // --- cover ---
  const img = $(body, "#cover-img");
  const none = $(body, "#cover-none");
  const removeBtn = $(body, "#cover-remove");
  let hasUpload = ctx.data.summary.has_cover_upload;
  const showCover = () => {
    img.hidden = true;
    none.hidden = false;
    img.onload = () => { img.hidden = false; none.hidden = true; };
    img.onerror = () => { img.hidden = true; none.hidden = false; };
    if (hasUpload || ctx.data.inspect.has_cover) img.src = api.coverUrl(ctx.id);   // nothing to show otherwise
    removeBtn.hidden = !hasUpload;
  };
  showCover();

  $(body, "#cover-file").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      await api.uploadCover(ctx.id, file);
      hasUpload = true;
      showCover();
      toast("Cover saved", "ok");
    } catch (err) { toast(err.message, "err"); }
    e.target.value = "";
  });
  removeBtn.addEventListener("click", async () => {
    if (!(await confirmBox({ title: "Remove your cover?", text: "The book's own cover (if it has one) will be used again.", okLabel: "Remove cover" }))) return;
    await api.removeCover(ctx.id);
    hasUpload = false;
    showCover();
    toast("Cover removed", "ok");
  });
}
