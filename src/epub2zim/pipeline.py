"""The high-level steps. The web UI, the CLI and the MCP server all call these.

    inspect_book   what kind of book is this, and which strategy fits?
    sample_pages   show a few page files as plain text (to look at a book)
    find_text      where does a word/phrase/pattern appear?
    suggest_titles make a title list automatically
    preview        split the book and report the articles (nothing is written)
    build          split, format and write the .zim file

Each function takes plain values (file path, settings, title list text), so it
can be used with or without the project folders in projects.py.
"""

from __future__ import annotations

import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from .article_edits import EditReport, edit_articles
from .autolink import AutoLinker
from .blocks import book_blocks
from .cleaning import detect_page_offset, raw_pages
from .epub_reader import Book, read_epub
from .formatter import format_html, format_text
from .projects import Project, slugify
from .propose import propose
from .settings import Settings
from .splitters import Article, SplitResult, split
from .titlelist import format_entries, parse, parse_aliases
from .zim_pages import CSS, article_page, home_page
from .zim_writer import ZimEntry, ZimPlan, make_icon, write_zim

# ISO 639-3 (used by ZIM) -> ISO 639-1 (used by HTML lang="..") for common languages.
_LANG2 = {"eng": "en", "deu": "de", "ger": "de", "fra": "fr", "fre": "fr", "spa": "es", "ita": "it",
          "por": "pt", "rus": "ru", "bul": "bg", "pol": "pl", "nld": "nl", "dut": "nl", "swe": "sv",
          "ces": "cs", "cze": "cs", "ukr": "uk", "jpn": "ja", "zho": "zh", "chi": "zh", "ara": "ar",
          "tur": "tr", "ell": "el", "gre": "el", "ron": "ro", "rum": "ro", "hun": "hu", "fin": "fi"}
_LANG3 = {v: k for k, v in _LANG2.items()}

# A tiny cache so the web UI doesn't re-read a big EPUB for every click.
_cache: dict[str, tuple[float, Book]] = {}


def load_book(path: str | Path) -> Book:
    path = Path(path)
    key, mtime = str(path.resolve()), path.stat().st_mtime
    if key in _cache and _cache[key][0] == mtime:
        return _cache[key][1]
    book = read_epub(path)
    _cache.clear()                     # keep only one book in memory
    _cache[key] = (mtime, book)
    return book


def zim_language(code: str) -> str:
    """'en' / 'en-US' / 'eng' -> 'eng' (ZIM files use 3-letter codes)."""
    code = (code or "").lower().split("-")[0].split("_")[0]
    return _LANG3.get(code, code) if len(code) == 2 else (code or "eng")


# ---------------------------------------------------------------------------
# Looking at a book
# ---------------------------------------------------------------------------
def inspect_book(path: str | Path) -> dict:
    """A short report on the book plus a suggested strategy and why."""
    book = load_book(path)
    blocks = book_blocks(book)
    headings = {lvl: 0 for lvl in range(1, 7)}
    for b in blocks:
        if b.heading_level:
            headings[b.heading_level] += 1
    pages = raw_pages(book)
    chars = sum(len(p) for p in pages)
    offset = detect_page_offset(pages)
    many_small_files = len(book.docs) >= 10 and chars / max(1, len(book.docs)) < 5000
    scanned = many_small_files and offset is not None and sum(headings.values()) < len(book.docs) / 10

    if scanned:
        strategy, why = "titles", ("Looks like a scanned book (one file per printed page, page numbers in the text, "
                                   "few real headings). Use a title list: in step 2, 'Fill from → Running headers' (or suggest_titles with method running_headers).")
    elif len(book.toc) >= 3:
        strategy, why = "toc", f"The book has a table of contents with {len(book.toc)} entries."
    elif sum(headings[l] for l in (1, 2, 3)) >= 3:
        lvl = 2 if headings[2] >= 3 else (1 if headings[1] >= 3 else 3)
        strategy, why = "headings", f"No useful table of contents, but {sum(headings.values())} headings were found (try level {lvl})."
    else:
        strategy, why = "files", "No table of contents or headings were found, so one article per file is safest."

    return {
        "title": book.title, "author": book.author, "language": book.language,
        "publisher": book.publisher, "description": book.description[:300],
        "files": len(book.docs), "characters": chars, "images": len(book.images),
        "has_cover": bool(book.cover_href), "toc_entries": len(book.toc),
        "toc_preview": [f"{'  ' * (t.level - 1)}{t.title}" for t in book.toc[:15]],
        "headings": {f"h{k}": v for k, v in headings.items() if v},
        "page_offset": offset, "looks_scanned": scanned,
        "suggested_strategy": strategy, "reason": why,
    }


def sample_pages(path: str | Path, start: int = 1, count: int = 3, chars: int = 400) -> list[dict]:
    """Plain text of a few page files (cut to `chars` each), to look inside a book."""
    pages = raw_pages(load_book(path))
    start = max(1, start)
    out = []
    for i in range(start, min(len(pages), start + max(1, min(count, 20)) - 1) + 1):
        text = pages[i - 1]
        out.append({"page": i, "chars": len(text), "text": text[:chars] + ("…" if len(text) > chars else "")})
    return out


def find_text(path: str | Path, query: str, regex: bool = False, limit: int = 20, context: int = 60) -> list[dict]:
    """Every page where `query` appears, with a little text around it."""
    if not query:
        return []
    rx = re.compile(query if regex else re.escape(query))
    out = []
    for i, text in enumerate(raw_pages(load_book(path)), start=1):
        for m in rx.finditer(text):
            a, b = max(0, m.start() - context), min(len(text), m.end() + context)
            out.append({"page": i, "match": m.group(0), "snippet": ("…" if a else "") + text[a:b] + ("…" if b < len(text) else "")})
            if len(out) >= limit:
                return out
    return out


def suggest_titles(path: str | Path, method: str, level: int = 2, pattern: str = "") -> str:
    """A title list (as text) made by one of the propose.py helpers."""
    entries = propose(load_book(path), method, level=level, pattern=pattern)
    header = f"# Suggested from: {method}. Check it, then edit freely.\n"
    return header + format_entries(entries) if entries else header + "# Nothing found with this method.\n"


# ---------------------------------------------------------------------------
# Splitting and building
# ---------------------------------------------------------------------------
@dataclass
class Prepared:
    book: Book
    result: SplitResult
    edits: EditReport


def _prepare(path: str | Path, settings: Settings, titles_text: str) -> Prepared:
    """Split the book, then rename / prefix / leave out articles (article_edits.py)."""
    book = load_book(path)
    entries = parse(titles_text) if settings.strategy == "titles" else None
    result = split(book, settings, entries)
    result.articles, edits = edit_articles(result.articles, settings)
    if not settings.description.strip():
        result.warnings.append(f"No description yet. The ZIM will say: “{_description(settings, book)}”. "
                               "Add your own in step 3 (max 80 characters).")
    return Prepared(book, result, edits)


def _description(settings: Settings, book: Book) -> str:
    """The description that goes into the ZIM (yours, else the book's, else a default)."""
    text = settings.description or (book.description and book.description[:80]) or "Converted from EPUB with epub2zim"
    return " ".join(text.split())[:80]


def _assign_paths(articles: list[Article]) -> None:
    """Give every article a unique, readable address like 'Chapter_One'."""
    used = {"index", "style.css"}
    for a in articles:
        base = re.sub(r"[^\w\-'(),.]+", "_", a.title.replace("/", "-")).strip("_")[:120] or "Article"
        path, n = base, 2
        while path.lower() in used or path.startswith("images"):
            path, n = f"{base}_{n}", n + 1
        used.add(path.lower())
        a.path = path


def preview(path: str | Path, settings: Settings, titles_text: str = "") -> dict:
    """Split the book and describe the result without writing anything."""
    prep = _prepare(path, settings, titles_text)
    arts = prep.result.articles
    return {
        "strategy": settings.strategy,
        "article_count": len(arts),
        "total_characters": sum(a.size for a in arts),
        "page_offset": prep.result.page_offset,
        "misses": prep.result.misses,
        "warnings": prep.result.warnings,
        "excluded": prep.edits.excluded,
        "articles": [
            {"n": i + 1, "title": a.title, "level": a.level, "group": a.group, "page": a.page,
             "chars": a.size, "renamed_from": prep.edits.renamed.get(a.title),
             "start": " ".join(re.sub(r"<[^>]+>", " ", a.content[:400]).split())[:90]}
            for i, a in enumerate(arts)
        ],
    }


def _parents(arts: list[Article], i: int) -> list[Article]:
    """Articles above article i in the hierarchy (closest last)."""
    chain, level = [], arts[i].level
    for j in range(i - 1, -1, -1):
        if arts[j].level < level:
            chain.insert(0, arts[j])
            level = arts[j].level
            if level <= 1:
                break
    return chain


def _children(arts: list[Article], i: int) -> list[Article]:
    out, level = [], arts[i].level
    for a in arts[i + 1:]:
        if a.level <= level:
            break
        if a.level == level + 1:
            out.append(a)
    return out


def build(path: str | Path, settings: Settings, out_path: str | Path, titles_text: str = "",
          aliases_text: str = "", cover_png: bytes | None = None) -> dict:
    """Make the .zim file. Returns a short report.

    cover_png: a cover you uploaded (PNG). Without it the book's own cover is used, if any.
    """
    started = time.time()
    prep = _prepare(path, settings, titles_text)
    book, arts = prep.book, prep.result.articles
    if not arts:
        raise ValueError("No articles were produced. Check the strategy and title list (try Preview first).")
    _assign_paths(arts)

    book_title = settings.title or book.title or Path(path).stem
    lang3 = zim_language(settings.language or book.language)
    lang2 = _LANG2.get(lang3, "en")

    # Where do HTML ids and files end up?  (for links inside the book)
    id_to_path = {i: a.path for a in arts for i in a.ids}
    doc_first_article: dict[int, str] = {}
    for a in arts:
        if a.page and a.page not in doc_first_article:
            doc_first_article[a.page] = a.path
    href_to_doc = {d.href: d.index for d in book.docs}

    def map_link(file_href: str, frag: str) -> str | None:
        if frag and frag in id_to_path:
            return f"{id_to_path[frag]}#{frag}"
        doc = href_to_doc.get(file_href)
        if doc is None:
            return None
        for i in range(doc, 0, -1):                       # article holding that file's start
            if i in doc_first_article:
                return doc_first_article[i]
        return None

    used_images: dict[str, str] = {}

    def map_image(href: str) -> str | None:
        if not settings.include_images or href not in book.images:
            return None
        used_images.setdefault(href, "images/" + re.sub(r"[^\w.\-]+", "_", href))
        return used_images[href]

    linker = AutoLinker({a.title: a.path for a in arts}, settings.autolink_min_length) if settings.autolink else None

    plan = ZimPlan(main_path="index", metadata={})
    for i, a in enumerate(arts):
        body = format_html(a.content, map_image, map_link) if a.kind == "html" else format_text(a.content, settings)
        if linker:
            body = linker.apply(body, a.path)
        page = article_page(
            title=a.title, content_html=body, book_title=book_title,
            parents=[(p.path, p.title) for p in _parents(arts, i)],
            children=[(c.path, c.title) for c in _children(arts, i)],
            prev=(arts[i - 1].path, arts[i - 1].title) if i > 0 else None,
            next_=(arts[i + 1].path, arts[i + 1].title) if i + 1 < len(arts) else None,
            page=a.page, from_scan=a.kind == "text", lang=lang2)
        plan.entries.append(ZimEntry(a.path, a.title, "text/html", page, front=True))

    # Cover: the one you uploaded, else the book's own. Used for the icon and the home page.
    cover, cover_mime = (cover_png, "image/png") if cover_png else \
        (book.images.get(book.cover_href, (None, ""))) if book.cover_href else (None, "")
    cover_path = None
    if cover and settings.cover_on_home:
        cover_path = "images/_epub2zim_cover" + {"image/jpeg": ".jpg", "image/gif": ".gif", "image/webp": ".webp"}.get(cover_mime, ".png")
        plan.entries.append(ZimEntry(cover_path, "Cover", cover_mime or "image/png", cover))

    plan.entries.append(ZimEntry("style.css", "style", "text/css", CSS))
    plan.entries.append(ZimEntry("index", book_title, "text/html", home_page(
        book_title=book_title, author=settings.creator or book.author,
        description=settings.description, lang=lang2, cover_path=cover_path,
        items=[(a.group, a.level, a.path, a.title) for a in arts]), front=True))
    for href, zpath in used_images.items():
        data, mime = book.images[href]
        plan.entries.append(ZimEntry(zpath, "", mime, data))

    # Aliases: extra names that open an article (shown in title search).
    by_title = {a.title.lower(): a.path for a in arts}
    paths = {e.path.lower() for e in plan.entries}
    alias_misses = []
    for alias, target in parse_aliases(aliases_text).items():
        target_path = by_title.get(target.lower())
        alias_path = re.sub(r"[^\w\-'(),.]+", "_", alias.replace("/", "-")).strip("_")
        if not target_path:
            alias_misses.append(f"{alias} = {target}")
        elif alias_path.lower() not in paths:
            paths.add(alias_path.lower())
            plan.redirects.append((alias_path, alias, target_path))

    plan.icon_png = make_icon(cover, book_title)
    name = settings.name or f"{slugify(book_title, 30).replace('-', '_')}_{lang2}"
    description = _description(settings, book)
    plan.metadata = {
        "Name": name, "Title": book_title[:30], "Language": lang3,
        "Description": description,
        "LongDescription": f"{book_title}" + (f" by {settings.creator or book.author}" if (settings.creator or book.author) else "")
                           + f". {len(arts)} articles, made with epub2zim.",
        "Creator": settings.creator or book.author or "Unknown",
        "Publisher": settings.publisher or "epub2zim",
        "Tags": "_category:other;ebook;_pictures:" + ("yes" if used_images else "no") + ";_videos:no;_details:yes",
        "Source": "epub2zim",
    }
    out = write_zim(plan, out_path, lang3)
    return {
        "file": str(out), "file_name": out.name, "size_bytes": out.stat().st_size,
        "articles": len(arts), "aliases": len(plan.redirects), "images": len(used_images),
        "misses": prep.result.misses, "alias_misses": alias_misses, "warnings": prep.result.warnings,
        "excluded": prep.edits.excluded,
        "seconds": round(time.time() - started, 1),
    }


# ---------------------------------------------------------------------------
# Project shortcuts (used by the web API and the MCP server)
# ---------------------------------------------------------------------------
def default_settings_from_book(project: Project) -> Settings:
    """First-time settings: metadata from the book, strategy from inspect_book."""
    report = inspect_book(project.epub_path)
    s = project.settings()
    s.title = s.title or report["title"]
    s.creator = s.creator or report["author"]
    s.language = zim_language(report["language"]) if report["language"] else s.language
    s.strategy = report["suggested_strategy"]
    if report["looks_scanned"]:
        s.detect_lists = False
    return s


def build_project(project: Project, output_copy_dir: Path | None = None) -> dict:
    s = project.settings()
    book_title = s.title or load_book(project.epub_path).title
    file_name = f"{slugify(s.name or book_title, 50)}_{time.strftime('%Y-%m')}.zim"
    report = build(project.epub_path, s, project.output_dir / file_name, project.titles(), project.aliases(),
                   cover_png=project.cover())
    if output_copy_dir:
        output_copy_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(report["file"], output_copy_dir / file_name)
        report["library_copy"] = str(output_copy_dir / file_name)
    return report
