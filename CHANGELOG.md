# Changelog

## 0.2.0 (2026-11-11)

From feedback converting a Bulgarian novel (chitanka.info):

- **Leave out articles**: an exclude list (with `*` wildcards) for title pages, credits and the
  like, and a ✕ button on every row of the preview.
- **Better titles**: chapters called only “I”, “II”, “3” or “Chapter 4” get their part's name in
  front (“Част първа · I”); plus a rename list (`Old title = New title`).
- **Parts and their first chapter** starting in the same file are both kept (the part lists
  its chapters) instead of being merged.
- **Cover upload**: your own cover for the library icon and the top of the home page (web UI,
  `set_cover` MCP tool, `--cover`). The book's own cover is still used by default.
- **Title list strategy keeps sentences**: the matched text is only removed from the article
  start when it looks like a heading; new `drop_heading_text` setting to switch it off.
- **Description reminder** in the preview and step 3 when the description is empty.
- **`delete_project` MCP tool** (asks for confirmation first).
- Readable file names for non-Latin titles (“Престъпление и наказание” →
  `prestaplenie-i-nakazanie`).
- The ZIM home page no longer uses a ✿ symbol that some readers can't display.

## 0.1.0 (2026-11-10)

First release.

- Convert EPUB books into searchable, wiki-style ZIM files (full-text search, title search,
  wiki-style links, aliases, pictures, cover icon).
- Four splitting strategies: table of contents, headings, one article per file, and a title
  list for scanned (OCR) books, with automatic suggestions from running headers or a pattern.
- Clean-up for scanned books: page numbers and running headers removed, paragraphs rebuilt,
  optional section headings and list detection.
- Web UI in the Blush design (light and Midnight themes) with a guided five-step flow.
- MCP server for AI assistants (Streamable HTTP with a Bearer key, or stdio), with guides
  for LM Studio and Open WebUI, plus skills for assistants.
- `epub2zim` command line, REST API, Docker image and compose file.
- Licensed under GPL-3.0-or-later.
