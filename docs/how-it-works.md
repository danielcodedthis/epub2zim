# How it works

From EPUB to ZIM in six stages. Each stage is one small module in `src/epub2zim/`.

```
 book.epub
    │  1. read          epub_reader.py   metadata, reading order, table of contents, images
    ▼
 Book
    │  2. blocks        blocks.py        each chapter file → paragraphs, headings, lists, tables…
    │     (or) clean    cleaning.py      scanned books: plain text per page, page numbers removed
    ▼
 blocks / page texts
    │  3. split         splitters/       toc | headings | files | titles  → articles
    ▼
 articles
    │  4. format        formatter.py     safe, tidy HTML; pictures and links pointed at new places
    │     link          autolink.py      mentions of other article titles become links
    ▼
 pages
    │  5. write         zim_pages.py     article pages, home page, style sheet
    │                   zim_writer.py    libzim: pages + images + aliases + metadata + search index
    ▼
 book.zim
```

`pipeline.py` runs these stages; the web UI, the CLI and the MCP server all call it.

## 1. Reading the EPUB

An EPUB is a zip file. `META-INF/container.xml` points to the *package* (`.opf`), which
lists every file (the *manifest*), the reading order (the *spine*) and metadata (title,
author, language). The table of contents is either EPUB 3 `nav` HTML or the older EPUB 2
`toc.ncx`; both are read. Images are kept so they can be copied into the ZIM.

## 2. Blocks

Each chapter file is broken into **blocks**: one paragraph, heading, list, table, picture…
A block remembers its file and every HTML `id` inside it. Table-of-contents links point at
those ids (`chapter2.xhtml#boats`), which is how a book can be cut in the middle of a file.
Links and image paths are rewritten as full paths inside the zip
(`epub:OEBPS/images/boat.png`) so they still work after splitting.

**Scanned books** go a different way: each page file becomes plain text, then
`cleaning.py` removes converter notes (“Page 12”), blank pages, printed page numbers and
running headers. To know which number on a page is the printed page number it detects the
**page offset** (file number − printed page number) by voting across all pages.

## 3. Splitting

The [strategy](splitting-strategies.md) decides where articles start. The result is a list
of articles, each with a title, a **level** (1 = top, 2 = inside the one above…), its
content (HTML or plain text) and the page file where it starts. Titles that a title list
asked for but that were not found are reported as **misses**.

## 4. Formatting and links

- **HTML articles:** only safe tags and attributes are kept (no scripts, styles or classes).
  Headings shift so the article title is the only `<h1>`. Pictures point to
  `images/…` inside the ZIM. Links to another part of the book point to the article holding
  that `id` (or the start of that file).
- **Text articles (scans):** paragraphs are rebuilt at sentence ends (~650 characters),
  *section headings* you listed become `<h2>`, and optional list detection puts
  `A. … B. …` / `1. … 2. …` items on their own lines.
- **Auto-links:** the first mention of another article's title (case-insensitive, also
  without a bracket part like “(Dysthymia)”) becomes a link, like on Wikipedia.

## 5. Writing the ZIM

Every article gets a readable address (`Major_Depressive_Disorder`; duplicates get `_2`).
Each page has a breadcrumb (book › parents), an *In this section* list of its children,
previous/next links, and for scans a small note about OCR. The home page lists all
articles grouped by the title list's `= Group` lines.

libzim then writes: all pages, the style sheet, the pictures, **aliases** as redirects,
metadata (title, description, language, creator, publisher, date, tags), a 48×48 icon
(from the cover, or a gradient tile), and builds the **title index** (search-as-you-type)
and the **full-text index** (search any word).

The file is written as `name.zim.part` and renamed when complete, so a half-written file is
never mistaken for a finished one.
