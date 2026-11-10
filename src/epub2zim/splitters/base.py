"""Shared pieces for all splitting strategies."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..blocks import Block


@dataclass
class Article:
    title: str
    level: int                 # 1 = top level, 2 = inside the one above, ...
    kind: str                  # "html" (content is HTML) or "text" (plain text from a scan)
    content: str
    page: int | None = None    # page file where it starts (shown as a hint)
    group: str | None = None   # group heading from the title list ("= Part One")
    ids: list[str] = field(default_factory=list)  # HTML ids inside (to fix internal links)
    path: str = ""             # filled in later: the article's address inside the ZIM

    @property
    def size(self) -> int:
        return len(self.content)


@dataclass
class SplitResult:
    articles: list[Article]
    misses: list[str] = field(default_factory=list)    # titles that could not be placed
    warnings: list[str] = field(default_factory=list)  # anything else worth telling the user
    page_offset: int | None = None                     # offset used for scanned books


def blocks_to_article(title: str, level: int, blocks: list[Block], drop_heading: bool = True) -> Article:
    """Join blocks into one HTML article.

    If the first block is a heading that repeats the title, it is dropped,
    because the article page already shows the title at the top.
    """
    if drop_heading and blocks and blocks[0].heading_level and _same(blocks[0].text, title):
        blocks = blocks[1:]
    return Article(
        title=title,
        level=level,
        kind="html",
        content="\n".join(b.html for b in blocks),
        page=blocks[0].doc_index if blocks else None,
        ids=[i for b in blocks for i in b.ids],
    )


def _same(a: str, b: str) -> bool:
    norm = lambda s: " ".join(s.lower().split()).strip(" .:")
    return norm(a) == norm(b) or norm(b).endswith(norm(a)) or norm(a).endswith(norm(b))


def front_matter(blocks: list[Block], min_chars: int = 200) -> Article | None:
    """Content before the first article, kept only if there is a fair amount of it."""
    if sum(len(b.text) for b in blocks) < min_chars:
        return None
    return blocks_to_article("Front matter", 1, blocks, drop_heading=False)
