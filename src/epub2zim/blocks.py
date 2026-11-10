"""Break chapter HTML into "blocks".

A block is one paragraph-sized piece of the book: a paragraph, a heading, a
list, a table, a picture, and so on. Working with a flat list of blocks makes
splitting simple: an article is just "blocks number 40 to 77".

Each block remembers:
  * which file it came from (doc_index)
  * every HTML id inside it, so table-of-contents links (file.xhtml#id)
    can be matched to the right block
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urldefrag

from bs4 import BeautifulSoup, NavigableString, Tag

from .epub_reader import Book, resolve_href

# Elements that are always one block each.
ATOMIC = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "dl", "table",
          "pre", "blockquote", "figure", "hr", "img", "svg"}
# Elements that may hold other blocks; we look inside them.
CONTAINERS = {"div", "section", "article", "main", "body", "aside", "header",
              "footer", "nav", "center"}
# Elements we drop completely.
SKIP = {"script", "style", "head", "title", "meta", "link", "noscript"}


@dataclass
class Block:
    doc_index: int
    tag: str
    html: str
    text: str
    ids: list[str] = field(default_factory=list)
    first_in_doc: bool = False

    @property
    def heading_level(self) -> int | None:
        """1-6 for <h1>-<h6>, otherwise None."""
        if len(self.tag) == 2 and self.tag[0] == "h" and self.tag[1].isdigit():
            return int(self.tag[1])
        return None


def _has_block_children(tag: Tag) -> bool:
    return tag.find(list(ATOMIC | CONTAINERS)) is not None


def _ids_in(tag: Tag) -> list[str]:
    ids = [tag["id"]] if tag.get("id") else []
    ids += [t["id"] for t in tag.find_all(id=True)]
    # Old-style anchors: <a name="x">
    ids += [t["name"] for t in tag.find_all("a", attrs={"name": True})]
    return ids


def _absolute_links(soup: BeautifulSoup, base_href: str) -> None:
    """Rewrite image and link addresses as full paths inside the EPUB zip.

    A chapter may say <img src="../images/a.png">; after splitting, the HTML no
    longer knows which file it came from, so we resolve it now. Results look
    like "epub:OEBPS/images/a.png" or "epub:OEBPS/ch2.xhtml#sec3".
    """
    for img in soup.find_all("img", src=True):
        img["src"] = "epub:" + resolve_href(base_href, img["src"])
    for img in soup.find_all("image"):          # <svg><image xlink:href=...>
        link = img.get("xlink:href") or img.get("href")
        if link:
            img["href"] = "epub:" + resolve_href(base_href, link)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        file_part, frag = urldefrag(href)
        target = resolve_href(base_href, file_part) if file_part else base_href
        a["href"] = "epub:" + target + (f"#{frag}" if frag else "")


def doc_blocks(doc_index: int, html: str, href: str | None = None) -> list[Block]:
    """Turn one HTML file into a list of blocks, in reading order."""
    soup = BeautifulSoup(html, "lxml")
    if href:
        _absolute_links(soup, href)
    body = soup.body or soup
    blocks: list[Block] = []
    pending_ids: list[str] = []      # ids of wrappers, given to the next block
    loose: list = []                  # inline bits lying directly in a container

    def emit(tag_name: str, html_text: str, text: str, ids: list[str]) -> None:
        nonlocal pending_ids
        text = " ".join(text.split())
        if not text and tag_name not in ("img", "figure", "hr", "svg", "table"):
            pending_ids += ids        # empty element: keep its ids for the next block
            return
        blocks.append(Block(doc_index, tag_name, html_text, text, pending_ids + ids))
        pending_ids = []

    def flush_loose() -> None:
        if not loose:
            return
        html_text = "".join(str(x) for x in loose)
        text = " ".join(x if isinstance(x, str) else x.get_text(" ") for x in loose)
        ids = [i for x in loose if isinstance(x, Tag) for i in _ids_in(x)]
        loose.clear()
        emit("p", f"<p>{html_text}</p>", text, ids)

    def walk(container: Tag) -> None:
        for child in container.children:
            if isinstance(child, NavigableString):
                if child.strip() and type(child) is NavigableString:  # skip comments etc.
                    loose.append(str(child))
                continue
            if not isinstance(child, Tag) or child.name in SKIP:
                continue
            name = child.name.lower()
            if name in ATOMIC:
                flush_loose()
                emit(name, str(child), child.get_text(" "), _ids_in(child))
            elif name in CONTAINERS and _has_block_children(child):
                flush_loose()
                if child.get("id"):
                    pending_ids.append(child["id"])
                walk(child)
                flush_loose()
            elif name in CONTAINERS:
                flush_loose()     # a container with only text acts like a paragraph
                emit("p", f"<p>{child.decode_contents()}</p>", child.get_text(" "), _ids_in(child))
            else:
                loose.append(child)  # inline element (span, a, em, ...)

    walk(body)
    flush_loose()
    if pending_ids and blocks:
        blocks[-1].ids += pending_ids
    if blocks:
        blocks[0].first_in_doc = True
    return blocks


def book_blocks(book: Book) -> list[Block]:
    """All blocks of the whole book, in reading order."""
    out: list[Block] = []
    for doc in book.docs:
        out.extend(doc_blocks(doc.index, doc.html, doc.href))
    return out
