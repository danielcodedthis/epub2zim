"""Tidy the article list after splitting: better titles and leaving articles out.

Runs for every strategy, in this order:

  1. renames        "Old title = New title" lines from the settings
  2. parent prefix  "I" under "Part One" becomes "Part One · I", so chapters that are
                    only numbered get a title you can find and search for
  3. exclude        articles whose title matches the exclude list are left out
                    (title page, credits, "Contents" ...). `*` matches anything,
                    matching ignores upper/lower case, and both the original and
                    the final title are checked.

Left-out articles are dropped with their text. Their sub-articles stay.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field

from .settings import Settings
from .splitters.base import Article

# Titles that say nothing on their own: Roman numerals, numbers, "Chapter 4", "Глава 4", "§ 3".
_SHORT = re.compile(
    r"^(?:(?:chapter|part|book|section|kapitel|chapitre|capítulo|глава|част|книга|раздел|§)\s*)?"
    r"(?:[IVXLCDM]+|[ivxlcdm]+|\d+[a-z]?)\.?$",
    re.IGNORECASE,
)


def is_short_title(title: str) -> bool:
    t = title.strip()
    return bool(_SHORT.match(t)) or len(t) <= 2


def parse_renames(lines: list[str]) -> dict[str, str]:
    out = {}
    for line in lines:
        if "=" in line:
            old, new = (s.strip() for s in line.split("=", 1))
            if old and new:
                out[old.lower()] = new
    return out


def _matches(title: str, patterns: list[str]) -> bool:
    t = title.strip().lower()
    return any(fnmatch.fnmatchcase(t, p.strip().lower()) for p in patterns if p.strip())


@dataclass
class EditReport:
    renamed: dict[str, str] = field(default_factory=dict)   # final title -> original title
    excluded: list[str] = field(default_factory=list)


def edit_articles(articles: list[Article], settings: Settings) -> tuple[list[Article], EditReport]:
    report = EditReport()
    renames = parse_renames(settings.renames)
    originals = [a.title for a in articles]

    # 1. renames
    for a in articles:
        new = renames.get(a.title.strip().lower())
        if new:
            a.title = new

    # 2. parent prefix (uses the parent's title after renames, before its own prefix)
    if settings.parent_prefix != "never":
        base_titles = [a.title for a in articles]
        for i, a in enumerate(articles):
            if a.level <= 1:
                continue
            if settings.parent_prefix == "short" and not is_short_title(base_titles[i]):
                continue
            parent = next((base_titles[j] for j in range(i - 1, -1, -1) if articles[j].level < a.level), None)
            if parent:
                a.title = f"{parent}{settings.prefix_separator}{base_titles[i]}"

    for a, original in zip(articles, originals):
        if a.title != original:
            report.renamed[a.title] = original

    # 3. leave out
    kept = []
    for a, original in zip(articles, originals):
        if settings.exclude and (_matches(a.title, settings.exclude) or _matches(original, settings.exclude)):
            report.excluded.append(a.title)
        else:
            kept.append(a)
    return kept, report
