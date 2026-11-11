"""Strategy "toc": one article per entry in the book's own table of contents.

Best for normal EPUBs from publishers, Calibre, Pandoc, Project Gutenberg...
Each TOC entry points to a file and (often) an id inside it. We find the block
holding that id and cut the book there.
"""

from __future__ import annotations

from ..blocks import Block
from ..epub_reader import Book
from .base import SplitResult, blocks_to_article, front_matter


def _find_block(blocks: list[Block], doc_index: int, fragment: str) -> int | None:
    """Index of the block where a TOC link lands."""
    if fragment:
        for i, b in enumerate(blocks):
            if b.doc_index == doc_index and fragment in b.ids:
                return i
    for i, b in enumerate(blocks):          # no id (or id not found): start of the file
        if b.doc_index >= doc_index:        # >= : an empty file falls through to the next one
            return i
    return None


def split_by_toc(book: Book, blocks: list[Block]) -> SplitResult:
    result = SplitResult(articles=[])
    if not book.toc:
        result.warnings.append("This book has no table of contents. Try the 'headings' or 'files' strategy.")
        return result

    # (block index, order in the TOC, title, level)
    starts: list[tuple[int, int, str, int]] = []
    level_at: dict[int, int] = {}        # deepest level already starting at each block
    for order, entry in enumerate(book.toc):
        doc = book.doc_by_href(entry.href)
        idx = _find_block(blocks, doc.index, entry.fragment) if doc else None
        if idx is None:
            result.misses.append(entry.title)
        elif idx in level_at and entry.level <= level_at[idx]:
            # Two entries of the same level at the same spot: keep the first one.
            result.warnings.append(f"'{entry.title}' starts at the same place as another entry; merged.")
        else:
            # A deeper entry at the same spot ("Part One" and its chapter "I") is kept:
            # the part becomes a short page listing its chapters, the chapter gets the text.
            level_at[idx] = entry.level
            starts.append((idx, order, entry.title, entry.level))

    starts.sort()
    if starts and starts[0][0] > 0:
        fm = front_matter(blocks[: starts[0][0]])
        if fm:
            result.articles.append(fm)
    for n, (idx, _, title, level) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(blocks)
        result.articles.append(blocks_to_article(title, level, blocks[idx:end]))
    return result
