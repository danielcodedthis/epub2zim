"""Tidy the plain text of scanned (OCR) books.

Scanned books converted to EPUB usually have one HTML file per printed page,
and each page still carries the page number and a "running header" (the
chapter or section name printed at the top of every page). Left alone, these
end up in the middle of sentences. This module removes them.

Words used here:
  * page file number  = position of the HTML file in the book (1, 2, 3, ...)
  * printed page      = the number printed on the paper page
  * page offset       = page file number minus printed page
"""

from __future__ import annotations

import re
from collections import Counter

from bs4 import BeautifulSoup

from .epub_reader import Book

# Text that some converters (e.g. the Internet Archive) add to every page.
_JUNK_PREFIXES = [
    re.compile(r"^Page \d+\s*"),
    re.compile(r"^The text on this page is estimated to be only [\d.]+% accurate\s*"),
]
_BLANK_PAGE = re.compile(r"^\s*This page (?:is )?intentionally left blank\.?\s*$", re.I)


def plain_text(html: str) -> str:
    """HTML -> one line of text with single spaces."""
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "head"]):
        t.decompose()
    return " ".join(soup.get_text(" ").split())


def raw_pages(book: Book) -> list[str]:
    """Plain text of every page file, with converter junk removed."""
    pages = []
    for doc in book.docs:
        text = plain_text(doc.html)
        for rx in _JUNK_PREFIXES:
            text = rx.sub("", text)
        if _BLANK_PAGE.match(text):
            text = ""
        pages.append(text)
    return pages


def detect_page_offset(pages: list[str], look_words: int = 12) -> int | None:
    """Guess the page offset by finding printed page numbers near the top of pages.

    For every page we collect the numbers among its first few words and see which
    "file number minus printed number" value turns up most often. Returns None
    when no clear answer exists (for example, a normal non-scanned book).
    """
    votes: Counter[int] = Counter()
    for i, text in enumerate(pages, start=1):
        head = text.split()[:look_words]
        tail = text.split()[-3:]
        for word in head + tail:
            if word.isdigit() and 0 < int(word) <= i:
                votes[i - int(word)] += 1
    if not votes:
        return None
    offset, count = votes.most_common(1)[0]
    return offset if count >= max(5, len(pages) // 5) else None


def strip_page_furniture(pages: list[str], offset: int | None, known_headers: list[str] | None = None) -> list[str]:
    """Remove printed page numbers and running headers from each page.

    Two layouts are handled:
      * "158 Chapter Name ...text"   (number first, typical for left pages)
      * "Section Name 157 ...text"   (number after the header, typical for right pages)
    `known_headers` (chapter/article titles) helps remove the first layout exactly.
    """
    if offset is None:
        return pages
    headers = sorted({h for h in (known_headers or []) if h}, key=len, reverse=True)
    out = []
    for i, text in enumerate(pages, start=1):
        printed = i - offset
        if printed < 1 or not text:
            out.append(text)
            continue
        num = str(printed)
        m = re.match(rf"^{num}\s*=?\s*", text)
        if m:                                   # "158 Chapter Name ..."
            text = text[m.end():]
            for h in headers:
                if text.startswith(h + " "):
                    text = text[len(h) + 1:]
                    break
        else:                                   # "Section Name 157 ..."
            m = re.match(rf"^([^.]{{3,140}}?)\s{num}\s", text)
            if m:
                text = text[m.end():]
        text = re.sub(rf"\s{num}$", "", text)   # page number at the foot
        out.append(text)
    return out


def text_pages(book: Book, *, clean: bool = True, page_offset: int | str | None = "auto",
               known_headers: list[str] | None = None) -> tuple[list[str], int | None]:
    """The book as a list of page texts, cleaned if asked.

    Returns (pages, offset_used). `page_offset` may be a number, "auto" or None.
    """
    pages = raw_pages(book)
    if not clean:
        return pages, None
    offset = detect_page_offset(pages) if page_offset == "auto" else page_offset
    if isinstance(offset, str):
        offset = int(offset) if offset.lstrip("-").isdigit() else None
    return strip_page_furniture(pages, offset, known_headers), offset
