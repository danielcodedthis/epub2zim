// Step 3: name the ZIM file and choose extras (links, pictures, aliases).

import { $, el, esc } from "../../dom.js";

export function renderDetails(ctx, body, head) {
  head.append(el(`<p class="hint">This is what your ZIM reader shows in its library. All optional except the title.</p>`));
  const s = ctx.settings;

  body.append(el(`
    <div>
      <fieldset class="group">
        <legend><span class="dot pink"></span>About the file</legend>
        <div class="form-grid">
          <label class="field"><span>Title</span><input class="input" id="title" maxlength="200"></label>
          <label class="field"><span>Author</span><input class="input" id="creator"></label>
          <label class="field"><span>Language <span class="hint">3 letters: eng, deu, fra, bul…</span></span><input class="input" id="language" maxlength="3"></label>
        </div>
        <label class="field"><span>Short description <span class="hint" id="desc-count"></span></span>
          <input class="input" id="description" maxlength="80" placeholder="One line about the book"></label>
        <details class="more"><summary>More file details</summary>
          <div class="form-grid" style="margin-top:10px">
            <label class="field"><span>Publisher</span><input class="input" id="publisher"></label>
            <label class="field"><span>Short name <span class="hint">letters, numbers, _</span></span><input class="input" id="name" placeholder="made from the title"></label>
          </div>
        </details>
      </fieldset>

      <fieldset class="group">
        <legend><span class="dot blue"></span>Extras</legend>
        <div class="checks">
          <label class="check"><input type="checkbox" id="autolink"> Link mentions of other article titles (like a wiki)</label>
          <label class="check"><input type="checkbox" id="images"> Include the book's pictures</label>
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
  const countDesc = () => { $(body, "#desc-count").textContent = `${desc.value.length}/80`; };
  desc.addEventListener("input", countDesc);
  countDesc();

  const autolink = $(body, "#autolink");
  autolink.checked = s.autolink;
  autolink.addEventListener("change", () => { ctx.settings.autolink = autolink.checked; ctx.changed("settings"); });
  const images = $(body, "#images");
  images.checked = s.include_images;
  images.addEventListener("change", () => { ctx.settings.include_images = images.checked; ctx.changed("settings"); });
  const minlen = $(body, "#minlen");
  minlen.value = s.autolink_min_length;
  minlen.addEventListener("change", () => { ctx.settings.autolink_min_length = Number(minlen.value) || 8; ctx.changed("settings"); });

  const aliases = $(body, "#aliases");
  aliases.value = ctx.aliases;
  aliases.addEventListener("input", () => { ctx.aliases = aliases.value; ctx.changed("aliases"); });
}
