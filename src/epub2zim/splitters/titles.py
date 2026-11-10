"""Strategy "titles": cut the book where the titles of YOUR title list appear.

Made for scanned (OCR) books, which have no usable table of contents or
headings: just one long stream of text, one file per printed page.

How it works:
  1. All pages are cleaned (page numbers and running headers removed) and
     joined into one long text, remembering where each page starts.
  2. For every entry, in order, we look for its search text (the title, or the
     "text to look for" column) from one page before its page to 3 pages after.
     Without a page we search from the previous match onwards.
  3. When the text appears more than once, we prefer the place that looks most
     like a heading (see _score).
  4. Each article runs from its match to the next one.

Titles that are never found are reported as "misses"; their text simply stays
in the article before them.
"""

from __future__ import annotations

import re

from ..cleaning import text_pages
from ..epub_reader import Book
from ..titlelist import Entry
from .base import Article, SplitResult

SEARCH_PAGES = 3   # how many pages after the given page to search
SEARCH_BEFORE = 1  # ...and how many before it (suggested pages are often one off)


def _score(stream: str, pos: int, page_start: bool) -> float:
    """Lower is better. Headings usually start a sentence; prose mentions don't.

    0   at the very start of a page or right after sentence-ending punctuation
    1   after a capitalised word (e.g. after a chapter name)
    5   after a lowercase word (probably a mention in a sentence) - used only as last resort
    99  inside quotation marks: never a heading
    """
    before = stream[max(0, pos - 3):pos]
    if before.endswith(("“", "‘", '"', "'")):
        return 99
    if page_start or pos == 0 or re.search(r"[.:;!?)\]]\s$", before):
        return 0
    prev_word = stream[max(0, pos - 40):pos].split()[-1:] or [""]
    if prev_word[0][:1].isupper() or prev_word[0][:1].isdigit():
        return 1
    return 5


def split_by_titles(book: Book, entries: list[Entry], *, clean: bool = True,
                    page_offset: int | str | None = "auto") -> SplitResult:
    result = SplitResult(articles=[])
    articles_entries = [e for e in entries if not e.is_group]
    if not articles_entries:
        result.warnings.append("The title list is empty. Add titles (or use 'Suggest titles') first.")
        return result

    headers = [e.title for e in entries] + [e.search_text for e in entries]
    pages, offset = text_pages(book, clean=clean, page_offset=page_offset, known_headers=headers)
    result.page_offset = offset

    # Join pages into one stream, remembering where each page starts.
    starts, parts, pos = [], [], 0
    for text in pages:
        starts.append(pos)
        parts.append(text)
        pos += len(text) + 1
    starts.append(pos)
    stream = " ".join(parts)
    page_starts = set(starts)

    def page_pos(page_no: int) -> int:
        """Character position where page file `page_no` (1-based) starts."""
        return starts[min(max(page_no, 1), len(pages)) - 1]

    found: list[tuple[int, Entry, str | None]] = []   # (position, entry, group)
    prev = -1
    group = None
    for e in entries:
        if e.is_group:
            group = e.title
            continue
        page = e.page
        if page is not None and e.printed:
            if offset is None:
                result.warnings.append(f"'{e.title}': printed page given but no page offset is known; searching from the previous title.")
                page = None
            else:
                page = page + offset
        lo = max(page_pos(page - SEARCH_BEFORE) if page else 0, prev + 1)
        hi = page_pos(page + SEARCH_PAGES + 1) if page else len(stream)
        if page and page + SEARCH_PAGES >= len(pages):
            hi = len(stream)

        best = None
        for m in re.finditer(re.escape(e.search_text), stream[lo:hi]):
            p = lo + m.start()
            s = _score(stream, p, p in page_starts)
            if best is None or s < best[0]:
                best = (s, p)
            if s == 0:
                break
        if best is None or best[0] >= 99:
            result.misses.append(e.title)
            continue
        found.append((best[1], e, group))
        prev = best[1]

    if found and found[0][0] > 200:
        result.articles.append(Article("Front matter", 1, "text", stream[: found[0][0]].strip(), page=1))
    for n, (p, e, grp) in enumerate(found):
        end = found[n + 1][0] if n + 1 < len(found) else len(stream)
        text = stream[p:end].strip()
        # Drop the heading words themselves; the page shows the title already.
        if text.startswith(e.search_text):
            text = text[len(e.search_text):].lstrip(" :.")
        if e.find and text.startswith(e.title):
            text = text[len(e.title):].lstrip(" :.")
        page_no = next(i for i in range(len(pages), 0, -1) if starts[i - 1] <= p)
        result.articles.append(Article(e.title, e.level, "text", text, page=page_no, group=grp))
    return result
