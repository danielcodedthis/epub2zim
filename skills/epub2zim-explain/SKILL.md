---
name: epub2zim-explain
description: Explain to a user what epub2zim is, how it turns an EPUB into a ZIM, which splitting strategy to choose, and how to use its web UI. Use for questions like "what does epub2zim do", "which option should I pick", "where is my file", or "why are some titles not found".
---

# Explaining epub2zim

Answer in plain words, short, and only as deep as the question. Point to the right step of
the web UI and to a doc file for more.

## The one-paragraph version

epub2zim takes an EPUB book, cuts it into articles (one per chapter, section or entry) and
packs them into a **ZIM file**: the offline format Kiwix uses for Wikipedia. The result has
a home page, links between articles and full-text search, and opens in Zimi, Kiwix or any
ZIM reader. It runs on the user's own computer (Docker or pip), at http://localhost:5100
by default.

## How it works (if asked)

1. Read the EPUB: metadata, reading order, table of contents, pictures.
2. Break chapters into blocks (paragraphs, headings…), or for scanned books, clean the page
   text (page numbers and running headers removed).
3. Split into articles with one of four strategies.
4. Tidy the HTML, point pictures/links to their new places, add wiki-style links.
5. Write the ZIM with a search index, aliases and an icon.
Doc: docs/how-it-works.md.

## The web UI, step by step

- **Books page:** drop an EPUB; your books are listed below.
- **Step 1 Look:** what was found + the suggested strategy; *Peek inside* reads pages and searches.
- **Step 2 Split:** pick a strategy card; *Title list* opens an editor with *Fill from* helpers.
- **Step 3 Name & extras:** cover (upload your own), title, language (3 letters), description
  (≤ 80), article titles (part names in front of "I", "II"…, renames, **leave out** pages),
  aliases, links, pictures.
- **Step 4 Preview:** list of articles, “not found” titles, very short/long ones, and a ✕ on
  each row to leave that article out. Nothing is written.
- **Step 5 Build:** the gradient button; then *Download*. A copy goes to `data/output`.
- **Settings page:** folders, MCP key and setup snippets, theme.
Changes save automatically. Doc: docs/web-ui.md.

## Which strategy?

| The book… | Choose |
|---|---|
| has a normal table of contents (most EPUBs) | **Table of contents** |
| has no/too short contents but real headings | **Headings** (level 2; 3 for smaller articles) |
| is a scan: hundreds of files, page numbers in the text | **Title list** (docs/scanned-books.md) |
| anything else | **One per file** |

## Common questions

- **Where is my file?** Step 5's Download button, and the data folder's `output/`.
- **Titles not found?** The title isn't spelled like in the book, or the page is off. Search
  it in step 1, copy the exact spelling (third column), fix the page. docs/troubleshooting.md.
- **Articles too big / too small?** Change strategy or heading level, or edit the title list.
- **Junk pages (title page, credits)?** ✕ in the preview, or the *Leave out* list in step 3.
- **Chapters only called "I", "II"?** *Short titles only* (the default) makes them "Part One · I";
  rename others in step 3.
- **Cover?** Step 3 → *Upload a cover…* (square, about 500×500). It's the library icon and sits
  on the home page.
- **Fix one article after building?** Not inside the ZIM; change the settings and build again
  (seconds). Leave out, rename and title list cover most fixes.
- **Can an AI do it?** Yes, via the MCP server; see the epub2zim-mcp-setup skill.
- **PDF?** Convert to EPUB with Calibre first; treat it like a scanned book.
- **Copyright:** convert books you have the right to use; don't share ZIMs of copyrighted books.

Full FAQ: docs/faq.md.
