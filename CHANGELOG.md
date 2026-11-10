# Changelog

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
