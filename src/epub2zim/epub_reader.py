"""Open an EPUB file and read what we need from it.

An EPUB is a zip file. Inside it:
  * META-INF/container.xml points to the "package" file (.opf)
  * the .opf lists the book's metadata, every file (the "manifest") and the
    reading order (the "spine")
  * a table of contents, either EPUB 3 "nav" HTML or the older EPUB 2 "toc.ncx"

This module turns all of that into a simple `Book` object. It does not change
or interpret the chapter HTML; that is the job of blocks.py.
"""

from __future__ import annotations

import posixpath
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urldefrag

from bs4 import BeautifulSoup

HTML_TYPES = {"application/xhtml+xml", "text/html"}


@dataclass
class Doc:
    """One HTML file from the reading order (usually a chapter, sometimes a page)."""
    index: int          # position in the reading order, starting at 1
    href: str           # path inside the zip, e.g. "OEBPS/chapter1.xhtml"
    html: str           # the raw HTML text


@dataclass
class TocEntry:
    """One line of the book's own table of contents."""
    level: int          # 1 = top level, 2 = nested once, ...
    title: str
    href: str           # file inside the zip
    fragment: str       # the part after '#', or "" if none


@dataclass
class Book:
    path: Path
    title: str = ""
    author: str = ""
    language: str = ""
    publisher: str = ""
    description: str = ""
    docs: list[Doc] = field(default_factory=list)
    toc: list[TocEntry] = field(default_factory=list)
    images: dict[str, tuple[bytes, str]] = field(default_factory=dict)  # href -> (bytes, mimetype)
    cover_href: str | None = None

    def doc_by_href(self, href: str) -> Doc | None:
        for d in self.docs:
            if d.href == href:
                return d
        return None


def resolve_href(base_file: str, link: str) -> str:
    """Turn a link found inside `base_file` into a full path inside the zip."""
    link = unquote(link)
    if link.startswith("/"):
        return link.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_file), link))


def _text(soup, name: str) -> str:
    """First metadata element with this name (namespace prefix ignored)."""
    tag = soup.find(lambda t: t.name and t.name.split(":")[-1] == name)
    return tag.get_text(" ", strip=True) if tag else ""


def read_epub(path: str | Path) -> Book:
    """Read an EPUB file into a Book. Raises ValueError if it is not a usable EPUB."""
    path = Path(path)
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise ValueError("This file is not an EPUB (it is not a zip archive).") from exc

    with zf:
        names = set(zf.namelist())

        def read(name: str) -> bytes:
            return zf.read(name)

        # 1. Find the package (.opf) file.
        if "META-INF/container.xml" not in names:
            raise ValueError("This EPUB has no META-INF/container.xml, so it cannot be read.")
        container = BeautifulSoup(read("META-INF/container.xml"), "xml")
        rootfile = container.find("rootfile")
        if not rootfile or rootfile.get("full-path") not in names:
            raise ValueError("The EPUB's container.xml does not point to a package file.")
        opf_path = rootfile["full-path"]
        opf = BeautifulSoup(read(opf_path), "xml")

        book = Book(path=path)
        book.title = _text(opf, "title") or path.stem
        book.author = _text(opf, "creator")
        book.language = _text(opf, "language")
        book.publisher = _text(opf, "publisher")
        book.description = _text(opf, "description")

        # 2. The manifest: every file in the book, by id.
        manifest: dict[str, dict] = {}
        for item in opf.find_all("item"):
            href = resolve_href(opf_path, item.get("href", ""))
            manifest[item.get("id", href)] = {
                "href": href,
                "type": item.get("media-type", ""),
                "props": item.get("properties", ""),
            }

        # 3. Images (kept so they can be copied into the ZIM file).
        for info in manifest.values():
            if info["type"].startswith("image/") and info["href"] in names:
                book.images[info["href"]] = (read(info["href"]), info["type"])
            if "cover-image" in info["props"]:
                book.cover_href = info["href"]
        if not book.cover_href:  # EPUB 2 style: <meta name="cover" content="item-id"/>
            meta = opf.find("meta", attrs={"name": "cover"})
            if meta and meta.get("content") in manifest:
                book.cover_href = manifest[meta["content"]]["href"]

        # 4. The spine: the reading order of the HTML files.
        for itemref in opf.find_all("itemref"):
            info = manifest.get(itemref.get("idref", ""))
            if not info or info["type"] not in HTML_TYPES or info["href"] not in names:
                continue
            html = read(info["href"]).decode("utf-8", errors="replace")
            book.docs.append(Doc(index=len(book.docs) + 1, href=info["href"], html=html))
        if not book.docs:
            raise ValueError("This EPUB has no readable chapters in its reading order.")

        # 5. Table of contents: prefer EPUB 3 nav, fall back to EPUB 2 NCX.
        nav = next((i for i in manifest.values() if "nav" in i["props"].split()), None)
        if nav and nav["href"] in names:
            book.toc = _read_nav(nav["href"], read(nav["href"]))
        if not book.toc:
            spine = opf.find("spine")
            ncx_id = spine.get("toc") if spine else None
            ncx = manifest.get(ncx_id) if ncx_id else None
            ncx = ncx or next((i for i in manifest.values() if i["type"] == "application/x-dtbncx+xml"), None)
            if ncx and ncx["href"] in names:
                book.toc = _read_ncx(ncx["href"], read(ncx["href"]))

        # Keep only TOC entries that point at files we actually read.
        spine_hrefs = {d.href for d in book.docs}
        book.toc = [t for t in book.toc if t.href in spine_hrefs and t.title]
        return book


def _read_nav(nav_href: str, data: bytes) -> list[TocEntry]:
    """EPUB 3: <nav epub:type="toc"> with nested <ol><li><a href=..>."""
    soup = BeautifulSoup(data, "lxml")
    nav = None
    for n in soup.find_all("nav"):
        if "toc" in (n.get("epub:type", "") + " " + n.get("role", "") + " " + n.get("id", "")):
            nav = n
            break
    nav = nav or soup.find("nav")
    if not nav or not nav.find("ol"):
        return []
    entries: list[TocEntry] = []

    def walk(ol, level: int) -> None:
        for li in ol.find_all("li", recursive=False):
            a = li.find(["a", "span"], recursive=False)
            if a is not None and a.name == "a" and a.get("href"):
                file_part, frag = urldefrag(a["href"])
                entries.append(TocEntry(level, a.get_text(" ", strip=True), resolve_href(nav_href, file_part), frag))
            child = li.find("ol", recursive=False)
            if child:
                walk(child, level + 1)

    walk(nav.find("ol"), 1)
    return entries


def _read_ncx(ncx_href: str, data: bytes) -> list[TocEntry]:
    """EPUB 2: <navMap><navPoint><navLabel><text>..</text></navLabel><content src=..>."""
    soup = BeautifulSoup(data, "xml")
    nav_map = soup.find("navMap")
    if not nav_map:
        return []
    entries: list[TocEntry] = []

    def walk(parent, level: int) -> None:
        for point in parent.find_all("navPoint", recursive=False):
            label = point.find("text")
            content = point.find("content")
            if label and content and content.get("src"):
                file_part, frag = urldefrag(content["src"])
                entries.append(TocEntry(level, label.get_text(" ", strip=True), resolve_href(ncx_href, file_part), frag))
            walk(point, level + 1)

    walk(nav_map, 1)
    return entries
