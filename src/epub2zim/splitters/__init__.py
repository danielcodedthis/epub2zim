"""The four ways to split a book into articles.

    toc       the book's own table of contents        (normal EPUBs)
    headings  every <h1>..<hN> heading                (no/poor table of contents)
    files     one article per HTML file               (simple fallback)
    titles    your own title list, matched in text    (scanned / OCR books)

Use `split(book, settings, entries)`; it picks the right one.
To add a new strategy: write a function returning SplitResult in a new file,
add its name to settings.STRATEGIES, and add a branch below.
"""

from __future__ import annotations

from ..blocks import book_blocks
from ..epub_reader import Book
from ..settings import Settings
from ..titlelist import Entry
from .base import Article, SplitResult
from .files import split_by_files
from .headings import split_by_headings
from .titles import split_by_titles
from .toc import split_by_toc

__all__ = ["Article", "SplitResult", "split"]


def split(book: Book, settings: Settings, entries: list[Entry] | None = None) -> SplitResult:
    if settings.strategy == "titles":
        offset = settings.page_offset.strip() if isinstance(settings.page_offset, str) else settings.page_offset
        return split_by_titles(book, entries or [], clean=settings.clean_text, page_offset=offset or None,
                               drop_heading=settings.drop_heading_text)
    blocks = book_blocks(book)
    if settings.strategy == "headings":
        return split_by_headings(blocks, settings.heading_level)
    if settings.strategy == "files":
        return split_by_files(book, blocks)
    return split_by_toc(book, blocks)
