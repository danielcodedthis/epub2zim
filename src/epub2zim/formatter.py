"""Turn an article's raw content into the tidy HTML shown in the ZIM file.

Two kinds of content come out of the splitters:

  * "html" (normal books): we keep the book's own HTML but clean it: only safe
    tags, headings shifted so the article title stays the biggest one, pictures
    and internal links pointed at their new places in the ZIM.
  * "text" (scanned books): plain text that lost its paragraphs in the scan. We
    rebuild paragraphs, optional section headings and optional numbered lists.
"""

from __future__ import annotations

import html as html_lib
import re
from typing import Callable

from bs4 import BeautifulSoup, Comment

from .settings import Settings

ALLOWED_TAGS = {
    "p", "br", "hr", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "dl", "dt", "dd",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "colgroup", "col",
    "blockquote", "pre", "code", "em", "strong", "b", "i", "u", "s", "sub", "sup", "small",
    "span", "a", "img", "figure", "figcaption", "abbr", "cite", "q", "mark", "div",
}
ALLOWED_ATTRS = {"href", "src", "alt", "title", "id", "colspan", "rowspan", "start", "type"}

# Callbacks the pipeline gives us to find new addresses.
ImageMapper = Callable[[str], "str | None"]       # "OEBPS/img/a.png" -> "images/OEBPS_img_a.png" or None
LinkMapper = Callable[[str, str], "str | None"]   # ("OEBPS/ch2.xhtml", "sec3") -> "Chapter_2#sec3" or None


# --------------------------------------------------------------------------
# HTML content (normal books)
# --------------------------------------------------------------------------
def format_html(content: str, map_image: ImageMapper, map_link: LinkMapper) -> str:
    soup = BeautifulSoup(f"<div id='__root'>{content}</div>", "lxml")
    root = soup.find(id="__root")

    for c in root.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()

    # Headings: the smallest number used becomes <h2> (the title is the <h1>).
    levels = [int(h.name[1]) for h in root.find_all(re.compile(r"^h[1-6]$"))]
    shift = 2 - min(levels) if levels else 0
    for h in root.find_all(re.compile(r"^h[1-6]$")):
        h.name = f"h{min(6, max(2, int(h.name[1]) + shift))}"

    # SVG pictures (common for covers): keep just the image inside.
    for svg in root.find_all("svg"):
        image = svg.find("image")
        if image and image.get("href"):
            new = soup.new_tag("img", src=image["href"], alt="")
            svg.replace_with(new)
        else:
            svg.decompose()

    for img in root.find_all("img"):
        src = img.get("src", "")
        new_src = map_image(src[5:]) if src.startswith("epub:") else None
        if new_src:
            img["src"] = new_src
        else:
            img.decompose()

    for a in root.find_all("a"):
        href = a.get("href", "")
        if href.startswith("epub:"):
            file_part, _, frag = href[5:].partition("#")
            target = map_link(file_part, frag)
            if target:
                a["href"] = target
            else:
                a.unwrap()
        elif not href.startswith(("http://", "https://", "mailto:")):
            a.unwrap()

    # Remove anything not on the allow-list (keeping the text inside it).
    for tag in root.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
        else:
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in ALLOWED_ATTRS}
    return root.decode_contents().strip()


# --------------------------------------------------------------------------
# Plain-text content (scanned books)
# --------------------------------------------------------------------------
def split_paragraphs(text: str, target: int = 650) -> list[str]:
    """Cut long text into paragraphs of roughly `target` characters, at sentence ends."""
    if len(text) < target * 1.5:
        return [text] if text else []
    sentences = re.split(r"(?<=[.?!”])\s+(?=[A-Z“(])", text)
    out, current = [], ""
    for s in sentences:
        current = (current + " " + s).strip()
        if len(current) >= target:
            out.append(current)
            current = ""
    if current:
        if out and len(current) < target // 3:
            out[-1] += " " + current
        else:
            out.append(current)
    return out


def split_list_items(text: str) -> list[str]:
    """Put "A. ...", "1. ...", "a. ..." items on their own lines."""
    t = re.sub(r"\s(?=(?:[A-Z]|\d{1,2})\.\s[A-Z“(])", "\n", text)
    t = re.sub(r"\s(?=[a-h]\.\s[A-Z])", "\n", t)
    return [x.strip() for x in t.split("\n") if x.strip()]


def _list_class(item: str) -> str:
    if re.match(r"^[A-Z]\.\s", item):
        return "li-a"
    if re.match(r"^\d{1,2}\.\s", item):
        return "li-1"
    if re.match(r"^[a-h]\.\s", item):
        return "li-i"
    return "li-x"


def format_text(text: str, settings: Settings) -> str:
    """Plain text -> HTML with paragraphs, optional headings and optional lists."""
    phrases = sorted({p for p in settings.subheadings if p.strip()}, key=len, reverse=True)
    if phrases:
        # A phrase counts as a heading at the start or after a sentence end,
        # and only when a capitalised word follows (so prose mentions are skipped).
        rx = re.compile(r"(?:(?<=^)|(?<=[.:;!?)\]”] ))(%s)(?= [A-Z“(])" % "|".join(map(re.escape, phrases)))
        pieces = rx.split(text)
    else:
        pieces = [text]

    out = []
    for i, piece in enumerate(pieces):
        piece = piece.strip()
        if not piece:
            continue
        if i % 2 == 1:                                   # a heading phrase
            out.append(f"<h2>{html_lib.escape(piece)}</h2>")
            continue
        if settings.detect_lists and re.search(r"(?:^|\s)(?:[A-Z]|\d{1,2})\.\s[A-Z]", piece):
            items = split_list_items(piece)
            if len(items) > 1:
                # The last item often swallows the prose that follows the list:
                # keep its first sentence in the list and treat the rest as paragraphs.
                tail = ""
                if len(items[-1]) > settings.paragraph_size:
                    first, _, rest = items[-1].partition(". ")
                    items[-1], tail = first + ".", rest
                out.append('<div class="items">' + "".join(
                    f'<p class="{_list_class(it)}">{html_lib.escape(it)}</p>' for it in items) + "</div>")
                for para in split_paragraphs(tail, settings.paragraph_size):
                    out.append(f"<p>{html_lib.escape(para)}</p>")
                continue
        for para in split_paragraphs(piece, settings.paragraph_size):
            out.append(f"<p>{html_lib.escape(para)}</p>")
    return "\n".join(out)
