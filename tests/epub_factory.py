"""Build small EPUB files for the tests (no real books needed).

    make_epub(...)          a normal book: chapters, table of contents, an image
    make_scanned_epub(...)  a "scanned" book: one file per printed page, no TOC,
                            page numbers and running headers in the text
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from PIL import Image

CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""


def _png(color=(232, 121, 159)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (60, 80), color).save(buf, "PNG")
    return buf.getvalue()


def _xhtml(title: str, body: str) -> str:
    return (f'<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml">'
            f"<head><title>{title}</title></head><body>{body}</body></html>")


def _write(path: Path, files: dict[str, str | bytes], manifest: list[str], spine: list[str],
           title: str, nav_toc: list[tuple[int, str, str]] | None, ncx: bool, cover: bool) -> Path:
    path = Path(path)
    items = "\n".join(manifest)
    spine_xml = "\n".join(f'<itemref idref="{i}"/>' for i in spine)
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="id">test-book</dc:identifier><dc:title>{title}</dc:title>
    <dc:creator>Test Author</dc:creator><dc:language>en</dc:language>
    <dc:description>A tiny book made for tests.</dc:description>
  </metadata>
  <manifest>{items}</manifest>
  <spine{' toc="ncx"' if ncx else ''}>{spine_xml}</spine>
</package>"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", CONTAINER)
        z.writestr("OEBPS/content.opf", opf)
        for name, data in files.items():
            z.writestr(name, data)
    return path


def make_epub(path, *, toc: str = "nav", with_headings: bool = True) -> Path:
    """Three chapters; chapter 2 has two sections (TOC links with #ids) and an image.

    toc = "nav" (EPUB 3), "ncx" (EPUB 2) or "none".
    """
    h = (lambda n, t, i="": f"<h{n}{f' id={chr(34)}{i}{chr(34)}' if i else ''}>{t}</h{n}>") if with_headings \
        else (lambda n, t, i="": f"<p{f' id={chr(34)}{i}{chr(34)}' if i else ''}><b>{t}</b></p>")
    chapters = {
        "ch1.xhtml": _xhtml("One", h(1, "The Lighthouse") + "<p>The lighthouse keeper watched the sea every night. "
                     "He wrote about the Harbour Master in his diary.</p><p>Second paragraph about storms.</p>"),
        "ch2.xhtml": _xhtml("Two", h(1, "The Harbour Master") + "<p>Introduction to the harbour.</p>"
                     + h(2, "Boats", "boats") + '<p>Boats came and went. See <a href="ch3.xhtml#end">the end</a>.</p>'
                     '<figure><img src="images/boat.png" alt="A boat"/><figcaption>A boat</figcaption></figure>'
                     + h(2, "Nets", "nets") + "<div><p>Nets were mended on Sundays.</p><ul><li>Big nets</li><li>Small nets</li></ul></div>"),
        "ch3.xhtml": _xhtml("Three", h(1, "Homecoming") + '<p>The lighthouse keeper came home.</p><p id="end">The end.</p>'),
    }
    files = {f"OEBPS/{k}": v for k, v in chapters.items()}
    files["OEBPS/images/boat.png"] = _png()
    files["OEBPS/images/cover.png"] = _png((94, 143, 224))
    manifest = [f'<item id="c{i}" href="{k}" media-type="application/xhtml+xml"/>' for i, k in enumerate(chapters, 1)]
    manifest += ['<item id="boat" href="images/boat.png" media-type="image/png"/>',
                 '<item id="cover" href="images/cover.png" media-type="image/png" properties="cover-image"/>']
    toc_entries = [(1, "The Lighthouse", "ch1.xhtml"), (1, "The Harbour Master", "ch2.xhtml"),
                   (2, "Boats", "ch2.xhtml#boats"), (2, "Nets", "ch2.xhtml#nets"), (1, "Homecoming", "ch3.xhtml")]
    if toc == "nav":
        # Build the nested <ol> list from (level, title, href) entries.
        html = "<ol>"
        for i, (lvl, t, href) in enumerate(toc_entries):
            nxt = toc_entries[i + 1][0] if i + 1 < len(toc_entries) else 1
            html += f'<li><a href="{href}">{t}</a>'
            if nxt > lvl:
                html += "<ol>"
            else:
                html += "</li>"
                if nxt < lvl:
                    html += "</ol></li>"
        html += "</ol>"
        files["OEBPS/nav.xhtml"] = _xhtml("Contents", f'<nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops">{html}</nav>')
        manifest.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
    if toc == "ncx":
        points = ""
        for i, (lvl, t, href) in enumerate(toc_entries):
            nxt = toc_entries[i + 1][0] if i + 1 < len(toc_entries) else 1
            points += f'<navPoint id="p{i}"><navLabel><text>{t}</text></navLabel><content src="{href}"/>'
            if nxt <= lvl:
                points += "</navPoint>" * (1 + lvl - nxt)
        files["OEBPS/toc.ncx"] = (f'<?xml version="1.0"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
                                  f"<navMap>{points}</navMap></ncx>")
        manifest.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
    return _write(path, files, manifest, [f"c{i}" for i in range(1, 4)], "The Harbour Book",
                  None, toc == "ncx", True)


# Sections of the fake scanned book: (title, pages of text). Each section starts with
# "<Title> Main Points" like a criteria heading, so title-list matching can be tested.
SCAN_SECTIONS = [
    ("Garden Basics", 6),
    ("Soil Care", 5),
    ("Watering Plants", 6),
    ("Pest Control", 5),
]
FRONT_PAGES = 4   # title page etc. before printed page 1 -> page offset = 4


def scanned_page_texts() -> list[str]:
    """Plain text of each page of the fake scanned book (before converting to HTML)."""
    pages = ["Page 1 THE GARDEN BOOK", "Page 2 Copyright notice for testing.",
             "Page 3 This page intentionally left blank", "Page 4 Contents Garden Basics Soil Care Watering Plants Pest Control"]
    printed = 1
    for title, n in SCAN_SECTIONS:
        for k in range(n):
            file_no = len(pages) + 1
            body = (f"{title} Main Points A. First rule of {title.lower()}. B. Second rule. "
                    if k == 0 else "")
            opener = ["Sunlight", "Compost", "Morning", "Seeds", "Weather", "Roots", "Mulch"][printed % 7]
            body += (f"{opener} {printed} is page {k + 1} of the {title.lower()} section. Plants need light. "
                     f"Read more in soil care later. The gardener checks every row carefully. ") * 4
            # running header: left pages "12 Chapter", right pages "Section 13"
            header = f"{printed} The Garden Book" if printed % 2 == 0 else f"{title} {printed}"
            if k == 0:
                header = ""                 # first page of a section has no header
            pages.append(f"Page {file_no} {header} {body}".replace("  ", " "))
            printed += 1
    return pages


def make_scanned_epub(path) -> Path:
    pages = scanned_page_texts()
    files, manifest = {}, []
    for i, text in enumerate(pages, start=1):
        files[f"OEBPS/page_{i}.html"] = _xhtml(f"Page {i}", f"<p>{text}</p>")
        manifest.append(f'<item id="p{i}" href="page_{i}.html" media-type="application/xhtml+xml"/>')
    return _write(path, files, manifest, [f"p{i}" for i in range(1, len(pages) + 1)], "The Garden Book",
                  None, False, False)
