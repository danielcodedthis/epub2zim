"""Strategy "files": one article per HTML file in the book.

The simplest option and the safest fallback: every chapter file becomes one
article. Titles come from the table of contents, else the first heading, else
"Part N".
"""

from __future__ import annotations

from ..blocks import Block
from ..epub_reader import Book
from .base import SplitResult, blocks_to_article


def split_by_files(book: Book, blocks: list[Block]) -> SplitResult:
    result = SplitResult(articles=[])
    toc_titles = {}
    for entry in book.toc:                     # first TOC title per file
        toc_titles.setdefault(entry.href, entry.title)

    for doc in book.docs:
        doc_blocks = [b for b in blocks if b.doc_index == doc.index]
        if not doc_blocks:
            continue                            # empty file (cover page with no text, etc.)
        heading = next((b.text for b in doc_blocks if b.heading_level), None)
        title = toc_titles.get(doc.href) or (heading[:150] if heading else f"Part {doc.index}")
        result.articles.append(blocks_to_article(title, 1, doc_blocks))
    return result
