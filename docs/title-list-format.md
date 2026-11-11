# Title list format

A plain-text plan of the articles to create. Used by the **title list** strategy; edited in
step 2 of the web UI, with `set_title_list` over MCP, or with `--titles file.txt` on the
command line. Parser: [`titlelist.py`](../src/epub2zim/titlelist.py).

## The rules

```
# Lines starting with # are comments. Empty lines are ignored.
= Part One                        a GROUP heading on the home page (not an article)
Chapter title                     a top-level article
- Section inside it               one dash per level of nesting
-- Deeper section
Title | 12                        starts on PAGE FILE 12 (1 = first file of the book)
Title | p.204                     starts on PRINTED page 204 (needs the page offset)
Title | 12 | Exact words          the words that start it in the text
```

Each entry has up to three columns separated by `|`:

1. **Title**: shown as the article title. Required.
2. **Page** (optional): where to start looking. A plain number is a *page file*; `p.123`
   is a *printed* page and is turned into a page file with the page offset
   (`page file = printed page + offset`).
3. **Text to look for** (optional): the exact words that begin the article in the book,
   if they differ from the title. Short heading-like text is removed from the article start;
   a whole sentence (when the book has no headings) is kept. Everything after the second `|` is used, so it may
   contain `|` itself (handy for OCR errors like `Bipolar | Disorder`).

## Example

```
= Section II: Diagnostic Criteria
Depressive Disorders | 199
- Major Depressive Disorder | 204
- Persistent Depressive Disorder (Dysthymia) | 212 | Persistent Depressive Disorder
= Appendix
Glossary of Technical Terms | p.817
```

## Tips

- **Order matters.** Titles are searched in list order, each after the previous one.
- **Copy the book's spelling**, including OCR mistakes. Use step 1's search to check.
- **Give pages** for short or common titles (“Prevalence”, “Notes”), otherwise they may
  match too early.
- **Use the third column** when the heading in the book is longer or different from the
  title you want, e.g. the book says “Motor Disorders Developmental Coordination Disorder”
  and you want the article called “Developmental Coordination Disorder”.
- Groups (`=`) only affect the home page; levels (`-`) affect breadcrumbs and the
  *In this section* lists.

## Aliases (a different file)

Aliases use `Short name = Article title`, one per line. See
[Aliases and extras](aliases-and-extras.md).
