"""The "title list": a plain-text plan of the articles to create.

It is what you edit in the web UI's big text box, what AI assistants send
through the MCP server, and what `--titles` reads on the command line.

Format (one entry per line):

    # Lines starting with # are comments.
    = Part One                        <- a group heading on the home page (not an article)
    Chapter title                     <- a top-level article
    - Section inside it               <- one dash per level of nesting
    -- Deeper section
    Title | 12                        <- optional: page file where it starts (1 = first file)
    Title | p.204                     <- optional: PRINTED page number (needs a page offset)
    Title | 12 | Text to look for     <- optional: the exact words that start it in the text

"Text to look for" defaults to the title itself. It is only used by the
"title list" splitting strategy (for scanned books). The other strategies use
the list only to rename or drop articles.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Entry:
    level: int               # 0 = group heading, 1 = article, 2 = nested article, ...
    title: str
    page: int | None = None  # page file number, or printed page if `printed` is True
    printed: bool = False
    find: str | None = None  # text that marks the start; None = use the title
    line: int = 0            # line number in the list (for error messages)

    @property
    def is_group(self) -> bool:
        return self.level == 0

    @property
    def search_text(self) -> str:
        return self.find or self.title


class TitleListError(ValueError):
    """Raised with a friendly message when a line cannot be understood."""


_PAGE = re.compile(r"^(p\.?\s*)?(-?\d+)$", re.I)


def parse(text: str) -> list[Entry]:
    entries: list[Entry] = []
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("="):
            entries.append(Entry(level=0, title=line.lstrip("= ").strip(), line=n))
            continue
        dashes = len(line) - len(line.lstrip("-"))
        parts = [p.strip() for p in line[dashes:].split("|", 2)]   # '|' may appear in the search text
        title = parts[0]
        if not title:
            raise TitleListError(f"Line {n}: the title is empty.")
        entry = Entry(level=dashes + 1, title=title, line=n)
        if len(parts) > 1 and parts[1]:
            m = _PAGE.match(parts[1])
            if not m:
                raise TitleListError(f"Line {n}: '{parts[1]}' is not a page number (use 12 or p.204).")
            entry.page = int(m.group(2))
            entry.printed = bool(m.group(1))
        if len(parts) > 2 and parts[2]:
            entry.find = parts[2]
        entries.append(entry)
    return entries


def format_entries(entries: list[Entry]) -> str:
    """The reverse of parse(): entries -> text."""
    lines = []
    for e in entries:
        if e.is_group:
            lines.append(f"= {e.title}")
            continue
        line = "-" * (e.level - 1) + (" " if e.level > 1 else "") + e.title
        page = (f"p.{e.page}" if e.printed else str(e.page)) if e.page is not None else ""
        if e.find and e.find != e.title:
            line += f" | {page} | {e.find}"
        elif page:
            line += f" | {page}"
        lines.append(line)
    return "\n".join(lines) + ("\n" if lines else "")


def parse_aliases(text: str) -> dict[str, str]:
    """Aliases (extra search names): one 'Short name = Article title' per line."""
    out: dict[str, str] = {}
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise TitleListError(f"Alias line {n}: use the form  Short name = Article title")
        alias, target = (s.strip() for s in line.split("=", 1))
        if alias and target:
            out[alias] = target
    return out
