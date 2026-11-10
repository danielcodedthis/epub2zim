"""Strategy "headings": start a new article at every heading (<h1> .. <hN>).

Good when the table of contents is missing or too coarse, as long as the book
uses real HTML headings. `max_level` 2 means: split at <h1> and <h2>.
"""

from __future__ import annotations

from ..blocks import Block
from .base import SplitResult, blocks_to_article, front_matter


def split_by_headings(blocks: list[Block], max_level: int = 2) -> SplitResult:
    result = SplitResult(articles=[])
    starts = [i for i, b in enumerate(blocks) if b.heading_level and b.heading_level <= max_level and b.text]
    if not starts:
        result.warnings.append(f"No headings <h1>..<h{max_level}> found. Try a higher level, or the 'files' strategy.")
        return result

    top = min(blocks[i].heading_level for i in starts)   # the biggest heading used becomes level 1
    if starts[0] > 0:
        fm = front_matter(blocks[: starts[0]])
        if fm:
            result.articles.append(fm)
    for n, idx in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(blocks)
        title = blocks[idx].text[:150]
        level = blocks[idx].heading_level - top + 1
        result.articles.append(blocks_to_article(title, level, blocks[idx:end]))
    return result
