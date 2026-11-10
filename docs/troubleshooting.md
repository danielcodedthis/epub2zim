# Troubleshooting

## Starting

**The page doesn't open.** Check it runs: `docker compose ps` / `docker compose logs`, or
the terminal where you started `epub2zim serve`. Open `http://localhost:5100/api/health`;
it should say `{"ok":true…}`. Another program on port 5100? Set `EPUB2ZIM_PORT`.

**“Permission denied” in the data folder (Docker).** Set `PUID`/`PGID` to your user
(`id -u`, `id -g`) in `.env` and restart.

**Can't open it from another device.** With pip, start with `--host 0.0.0.0`. Check the
firewall allows the port.

## Adding a book

**“That file is not an EPUB”.** The file isn't a zip-based EPUB (maybe a PDF or MOBI
renamed). Convert it with Calibre first.

**“larger than 300 MB”.** Raise `EPUB2ZIM_MAX_UPLOAD_MB`, or copy the file to `inbox/`
and import with the CLI or MCP.

## Splitting

**Everything ends up in one article.** The strategy found nothing to split at. Look at
step 1: no contents entries → try *Headings*; no headings → *One per file* or a title list.

**Articles are too big.** Contents list only has chapters: use *Headings* with level 2–3.

**Lots of tiny articles.** Headings level too deep: lower it. Title list: titles matched
mentions instead of headings. Add page numbers or the exact starting words.

**Titles “not found” (title list).**
- Search the title in step 1. OCR often changes letters (`I` → `|` or `l`, `rn` → `m`).
  Copy the book's spelling, or put the exact text in the third column.
- The page may be off. Search shows the real page file. A printed page needs `p.` in front.
- An earlier title matched too late and the search window moved past it. Fix the earlier one first.

**Page numbers or headers still in the text (scans).** Check *Remove page numbers and
running headers* is on and the page offset is right (step 1 shows the detected one). If
detection fails, enter the offset: page file number of printed page 1, minus 1.

**Headings inside scanned articles are missing.** Add the phrases under *Section headings*,
spelled as in the book. They only count at a sentence start and before a capital letter.

## Building

**Build is slow.** Search indexing takes time for big books (a 1,000-page book: about
10–60 seconds). Pictures add size and time; switch them off if not needed.

**“description must be 80 characters or fewer”.** A ZIM rule. Shorten it.

**The reader shows an old version.** Readers cache files. Remove the old ZIM from the
reader's library and add the new one; kiwix-serve needs a restart.

## AI assistants

See [LM Studio](lm-studio.md#tips) and [Open WebUI](open-webui.md#troubleshooting).
Quick checks: the URL ends with `/mcp`; the key is sent as `Authorization: Bearer <key>`;
`401` means the key is wrong; inside Docker, use `host.docker.internal` instead of
`localhost`.
