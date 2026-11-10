"""Suggest a title list automatically, so nobody has to start from a blank page.

Four helpers, each returning a list of titlelist.Entry:

    from_toc(book)                  the book's table of contents
    from_headings(book, level)      the book's <h1>..<hN> headings
    from_running_headers(book)      for scanned books: the header printed on each page
    from_pattern(book, regex)       every match of a regular expression (one group = the title)

The suggestions are a starting point. Review them (web UI step 3) before building.
"""

from __future__ import annotations

import re

from .blocks import book_blocks
from .cleaning import detect_page_offset, raw_pages
from .epub_reader import Book
from .titlelist import Entry


def from_toc(book: Book) -> list[Entry]:
    page_of = {d.href: d.index for d in book.docs}
    return [Entry(level=t.level, title=t.title, page=page_of.get(t.href)) for t in book.toc]


def from_headings(book: Book, max_level: int = 2) -> list[Entry]:
    blocks = [b for b in book_blocks(book) if b.heading_level and b.heading_level <= max_level and b.text]
    if not blocks:
        return []
    top = min(b.heading_level for b in blocks)
    return [Entry(level=b.heading_level - top + 1, title=b.text[:150], page=b.doc_index) for b in blocks]


def _common_prefix_words(a: str, b: str, max_words: int = 14) -> str:
    out = []
    for x, y in zip(a.split()[:max_words], b.split()[:max_words]):
        if x != y:
            break
        out.append(x)
    return " ".join(out)


def from_running_headers(book: Book, min_pages: int = 2) -> list[Entry]:
    """Scanned books: read the running header printed at the top of each page.

    Right-hand pages often look like "Section Name 157 ..." and left-hand pages
    like "158 Chapter Name ...". We collect the header of every page, then turn
    each run of pages sharing a header into one entry. Best effort: expect to
    fix some titles by hand.
    """
    pages = raw_pages(book)
    offset = detect_page_offset(pages)
    if offset is None:
        return []
    headers: list[str | None] = [None] * len(pages)
    for i, text in enumerate(pages, start=1):
        num = str(i - offset)
        m = re.match(rf"^([^.\d]{{3,140}}?)\s{num}\s", text)        # "Header 157 ..."
        if m:
            headers[i - 1] = m.group(1).strip()
        elif text.startswith(num + " ") and i + 2 <= len(pages):    # "158 Header ..."
            nxt = pages[i + 1]                                      # the next left-hand page
            nnum = str(i + 2 - offset)
            if nxt.startswith(nnum + " "):
                common = _common_prefix_words(text[len(num) + 1:], nxt[len(nnum) + 1:])
                if 1 <= len(common.split()) <= 12:
                    headers[i - 1] = common

    entries: list[Entry] = []
    seen: set[str] = set()
    for i in range(1, len(headers) + 1):
        h = headers[i - 1]
        prev = headers[i - 2] if i > 1 else None
        if h and h != prev and h not in seen:
            # How many pages (looking at every other page too) carry this header?
            count = sum(1 for x in headers[i - 1:i + 30] if x == h)
            if count >= min_pages:
                seen.add(h)
                # The first page of a section usually has no header: start one page earlier.
                entries.append(Entry(level=1, title=h, page=max(1, i - 1)))
    return entries


def from_pattern(book: Book, pattern: str, max_results: int = 500) -> list[Entry]:
    """Every match of `pattern` becomes a title. Use one (group) for the title part.

    Example for a book whose sections start with "<Name> Diagnostic Criteria":
        ((?:[A-Z][\\w'/-]+ ){1,8})Diagnostic Criteria
    """
    rx = re.compile(pattern)
    pages = raw_pages(book)
    entries, seen = [], set()
    for i, text in enumerate(pages, start=1):
        for m in rx.finditer(text):
            title = (m.group(1) if m.groups() else m.group(0)).strip()
            if title and title not in seen:
                seen.add(title)
                entries.append(Entry(level=1, title=title, page=i))
                if len(entries) >= max_results:
                    return entries
    return entries


def propose(book: Book, method: str, *, level: int = 2, pattern: str = "") -> list[Entry]:
    """Pick a helper by name: toc | headings | running_headers | pattern."""
    if method == "toc":
        return from_toc(book)
    if method == "headings":
        return from_headings(book, level)
    if method == "running_headers":
        return from_running_headers(book)
    if method == "pattern":
        if not pattern:
            raise ValueError("Give a regular expression for the 'pattern' method.")
        return from_pattern(book, pattern)
    raise ValueError("method must be toc, headings, running_headers or pattern")
