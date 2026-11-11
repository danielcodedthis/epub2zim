# Splitting strategies

A ZIM file is a collection of articles. The **strategy** decides where one article ends
and the next begins. Step 1 of the web UI (or `inspect_book` / `epub2zim inspect`)
suggests one and says why.

| Strategy | Setting value | Cuts the book at… | Best for |
|---|---|---|---|
| Table of contents | `toc` | every entry of the book's own contents | Most EPUBs |
| Headings | `headings` | every `<h1>`…`<hN>` | No / too-short contents list |
| One per file | `files` | every HTML file | Fallback |
| Title list | `titles` | where your titles appear in the text | Scanned (OCR) books |

## `toc`: table of contents

Uses the EPUB 3 `nav` or EPUB 2 `toc.ncx`. Nested entries become nested articles
(level 2, 3…), so a chapter with sections becomes a chapter page plus one page per section,
and the chapter page lists them under *In this section*.

- An entry pointing to `file.xhtml#id` starts at the block holding that id; an entry
  without `#id` starts at the top of the file.
- A part and its first chapter at the same spot (“Part I” and “Chapter 1”) are both kept:
  the part becomes a short page listing its chapters. Two entries of the *same* level at the
  same spot are merged, with a warning.
- Text before the first entry (cover, copyright…) becomes **Front matter** if it is longer
  than 200 characters.

**Tip:** if the articles are too big (the contents only lists chapters), try `headings`
with level 2 or 3.

## `headings`: every heading

Starts a new article at each heading down to `heading_level` (default 2: `<h1>` and
`<h2>`). The biggest heading used becomes level 1. Good for Pandoc/Markdown-made books and
books whose contents list is missing.

**Tip:** level 1 gives few, long articles; level 3 many, short ones.

## `files`: one article per file

Every HTML file of the reading order becomes one article. The title comes from the
contents list, else the first heading, else “Part N”. Empty files are skipped. Use it when
nothing else fits; it always works.

## `titles`: your title list

For books without usable structure, typically **scans**: hundreds of files, one per
printed page, no headings, page numbers and running headers mixed into the text.

You give a [title list](title-list-format.md). For each title, in order, epub2zim:

1. cleans and joins all pages into one long text (page numbers and headers removed);
2. searches for the title (or the *text to look for*) from **one page before** the page you
   gave to **three pages after** it, never before the previous title;
3. if it appears several times, prefers the place that looks like a heading: start of a
   page or right after a sentence end, then after a capitalised word; mentions inside a
   sentence are a last resort, and text in quotation marks is never used;
4. starts the article there; it runs to the next title. The heading words are removed from
   the start of the article (the page shows the title already), but **only if they look like
   a heading**: at most 12 words, not ending like a sentence. A full sentence used as *text to
   look for* is always kept. Switch removal off with *Remove the matched heading words*
   (`drop_heading_text`).

Titles that are never found are listed as **misses**; their text stays in the previous
article. Without a page number the search runs from the previous title to the end of the
book: fine for distinctive titles, risky for common words.

Don't want to type the list? Use **Fill from**: table of contents, headings,
**running headers** (reads the header printed at the top of scanned pages) or a
**pattern** (regular expression). Then fix it. Full walkthrough:
[Scanned books](scanned-books.md).

## Adding a strategy

See [Architecture → Adding a splitting strategy](architecture.md#adding-a-splitting-strategy).
