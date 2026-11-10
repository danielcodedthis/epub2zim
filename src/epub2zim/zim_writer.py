"""Write the .zim file with python-libzim.

A ZIM file holds: pages (HTML), files (CSS, images), "redirects" (extra names
that open another page), metadata (title, language, ...) and an icon. libzim
builds the title index and the full-text search index for us.
"""

from __future__ import annotations

import contextlib
import datetime
import io
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from libzim.writer import Creator, Hint, Item, StringProvider


@dataclass
class ZimEntry:
    path: str
    title: str
    mimetype: str
    content: bytes | str
    front: bool = False      # True = a real article (shown in search results)


@dataclass
class ZimPlan:
    """Everything that goes into one ZIM file."""
    main_path: str
    metadata: dict[str, str]
    entries: list[ZimEntry] = field(default_factory=list)
    redirects: list[tuple[str, str, str]] = field(default_factory=list)  # (path, title, target path)
    icon_png: bytes | None = None


class _Item(Item):
    """Adapter between our ZimEntry and libzim's Item interface."""

    def __init__(self, entry: ZimEntry):
        super().__init__()
        self.entry = entry

    def get_path(self):
        return self.entry.path

    def get_title(self):
        return self.entry.title

    def get_mimetype(self):
        return self.entry.mimetype

    def get_contentprovider(self):
        return StringProvider(self.entry.content)

    def get_hints(self):
        return {Hint.FRONT_ARTICLE: self.entry.front}


def make_icon(cover: bytes | None, title: str) -> bytes:
    """48x48 PNG: the book cover if there is one, otherwise a Blush gradient tile."""
    from PIL import Image, ImageDraw, ImageFont

    size = 48
    if cover:
        try:
            im = Image.open(io.BytesIO(cover)).convert("RGBA")
            side = min(im.size)
            left, top = (im.width - side) // 2, 0          # keep the top of the cover (title area)
            im = im.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "PNG")
            return buf.getvalue()
        except Exception:
            pass                                            # unreadable cover: fall through
    im = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(im)
    a, b = (0x5E, 0x8F, 0xE0), (0xE8, 0x79, 0x9F)          # Blush blue -> pink
    for y in range(size):
        t = y / (size - 1)
        draw.line([(0, y), (size, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    letters = "".join(w[0] for w in title.split()[:2]).upper() or "Z"
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    w = draw.textlength(letters, font=font)
    draw.text(((size - w) / 2, 12), letters, font=font, fill="white")
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


@contextlib.contextmanager
def _stdout_to_stderr():
    """libzim prints progress to standard output. In MCP "stdio" mode standard
    output carries the protocol, so we point it at standard error meanwhile."""
    try:
        sys.stdout.flush()
        saved = os.dup(1)
        os.dup2(2, 1)
    except (OSError, ValueError):       # no real file descriptors (e.g. some test runners)
        yield
        return
    try:
        yield
    finally:
        os.dup2(saved, 1)
        os.close(saved)


def write_zim(plan: ZimPlan, out_path: str | Path, language: str = "eng") -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".zim.part")       # write to a temp name, rename when done
    if tmp.exists():
        tmp.unlink()

    meta = {"Date": datetime.date.today().isoformat(), **plan.metadata}
    with _stdout_to_stderr(), Creator(str(tmp)).config_verbose(False).config_indexing(True, language or "eng") as creator:
        creator.set_mainpath(plan.main_path)
        if plan.icon_png:
            creator.add_illustration(plan.icon_png, 48)
        for key, value in meta.items():
            if value:
                creator.add_metadata(key, value)
        for entry in plan.entries:
            creator.add_item(_Item(entry))
        for path, title, target in plan.redirects:
            creator.add_redirection(path, title, target, {Hint.FRONT_ARTICLE: True})
    tmp.replace(out_path)
    return out_path
