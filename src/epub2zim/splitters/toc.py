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

    starts: list[tuple[int, str, int]] = []  # (block index, title, level)
    seen: set[int] = set()
    for entry in book.toc:
        doc = book.doc_by_href(entry.href)
        idx = _find_block(blocks, doc.index, entry.fragment) if doc else None
        if idx is None:
            result.misses.append(entry.title)
        elif idx in seen:
            # Two TOC entries at the same spot (e.g. "Part 1" and "Chapter 1"): keep the first.
            result.warnings.append(f"'{entry.title}' starts at the same place as another entry; merged.")
        else:
            seen.add(idx)
            starts.append((idx, entry.title, entry.level))

    starts.sort()
    if starts and starts[0][0] > 0:
        fm = front_matter(blocks[: starts[0][0]])
        if fm:
            result.articles.append(fm)
    for n, (idx, title, level) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(blocks)
        result.articles.append(blocks_to_article(title, level, blocks[idx:end]))
    return result
