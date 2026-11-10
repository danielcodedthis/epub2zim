---
name: epub2zim-scanned-books
description: Build and fix a title list so epub2zim can split a scanned (OCR) EPUB into proper articles. Use when inspect_book says looks_scanned or suggests the "titles" strategy, or when a book has one file per printed page.
---

# Convert a scanned book with a title list

Scanned EPUBs have one file per printed page, no table of contents and no headings. The
`titles` strategy cuts the text where the titles of a **title list** appear. Your job:
build a good list, check it with previews, fix it, then build.

## Title list format (one line per entry, in book order)

```
= Group heading          (home page only, not an article)
Chapter title | 45       (starts on page file 45; 1 = first file)
- Section | p.120        (one dash per level; p.120 = PRINTED page 120)
- Short name | 130 | Exact words that start it in the text
# comment
```

## Steps

1. **Understand the book.** `inspect_book` → note `files` and `page_offset`
   (page file = printed page + offset). Use `read_pages` on 2–3 pages in the middle to see
   how section headings look in the text.

2. **Get a first list.** Try in this order and keep the best:
   - `suggest_titles(method="running_headers")`: section names printed at the top of pages.
   - `suggest_titles(method="pattern", pattern=...)` when sections start with a fixed phrase.
     The `( )` group becomes the title. Example:
     `((?:[A-Z][\w'’/,()-]+ ){1,10})Diagnostic Criteria`. Test it first with
     `find_text(query=..., regex=true)`.
   - `suggest_titles(method="toc")` if a partial contents list exists.
   Save the chosen one with `save=true` (ask the user first if a list already exists).

3. **Clean it.** With `get_title_list` look for entries that are not sections (the book
   title, "Contents", "Index", page furniture) and remove them with
   `replace_in_title_list(old="<the line>\n", new="")`. Add `=` groups and `-` levels if
   the book has parts/chapters/sections. For many changes, write the whole list with
   `set_title_list`.

4. **Preview.** `update_settings {"strategy": "titles"}` then `preview_split(show=30)`.
   Fix in this order, previewing after each batch:
   - **MISSES:** `find_text(query="<title>")`. If found, copy the book's exact spelling
     (OCR errors included, e.g. "Bipolar | Disorder") into the third column, and set the
     page to the page file shown. If not found, try fewer words.
   - **Very short articles** (under ~150 characters): the title matched a mention. Add or
     correct the page number.
   - **Very long articles:** a section is missing from the list. Look at pages in that
     range with `read_pages` and add it.
   - The `start` column should be the beginning of that section's text.

5. **Make articles readable.** `update_settings` with
   - `subheadings`: list of phrases that start sub-sections (e.g. ["Diagnostic Features",
     "Prevalence", "Differential Diagnosis"]) → they become headings;
   - `detect_lists: true` if the book has "A. … B. …" or "1. … 2. …" criteria.

6. **Aliases and build.** Optional `set_aliases` for abbreviations, then `build_zim`.
   Report misses that remain; their text is inside the previous article.

## Tips

- Work in batches; don't fix one title per preview on long books.
- Pages are **page files**. Printed page numbers need `p.` in front.
- A wrong early match shifts later searches: fix problems from the top of the list down.
- It is fine to leave a few misses if the user is happy; say so clearly.

Details: docs/scanned-books.md and docs/title-list-format.md.
