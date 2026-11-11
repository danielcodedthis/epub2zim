"""Projects: one folder per book inside the data folder.

    <data>/projects/<project-id>/
        book.epub        the uploaded or imported book (never modified)
        project.json     settings (see settings.py) + name and dates
        titles.txt       the title list (see titlelist.py)
        aliases.txt      extra search names ("PTSD = Posttraumatic Stress Disorder")
        cover.png        optional cover you uploaded (replaces the book's own cover)
        output/          finished .zim files

Every finished .zim is also copied to <data>/output/ so a ZIM reader such as
Zimi or kiwix-serve can watch a single folder.
"""

from __future__ import annotations

import io
import json
import re
import secrets
import shutil
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .settings import Settings

_ID_OK = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")


class ProjectError(ValueError):
    """A friendly error about projects (unknown id, bad file name, ...)."""


# Cyrillic -> Latin, so "Престъпление и наказание" gives a readable file name
# ("prestaplenie-i-nakazanie") instead of "book". Bulgarian/Russian/Ukrainian letters.
_CYRILLIC = dict(zip(
    "абвгдежзийклмнопрстуфхцчшщъыьэюяёєіїґ",
    ["a", "b", "v", "g", "d", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
     "f", "h", "ts", "ch", "sh", "sht", "a", "y", "", "e", "yu", "ya", "yo", "ye", "i", "yi", "g"],
))


def slugify(text: str, limit: int = 40) -> str:
    """'Moby-Dick; or, The Whale' -> 'moby-dick-or-the-whale' (used for ids and file names)."""
    text = "".join(_CYRILLIC.get(ch, ch) for ch in text.lower())
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()   # é -> e, ü -> u
    s = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return s[:limit].strip("-") or "book"


COVER_MAX = 1000   # pixels: uploaded covers are shrunk to fit inside 1000x1000


@dataclass
class Project:
    id: str
    dir: Path

    # --- files ---------------------------------------------------------
    @property
    def epub_path(self) -> Path:
        return self.dir / "book.epub"

    @property
    def output_dir(self) -> Path:
        return self.dir / "output"

    def _read(self, name: str, default: str = "") -> str:
        p = self.dir / name
        return p.read_text(encoding="utf-8") if p.exists() else default

    def _write(self, name: str, text: str) -> None:
        (self.dir / name).write_text(text, encoding="utf-8")

    # --- info (name, dates, original file name) -------------------------
    def info(self) -> dict:
        data = json.loads(self._read("project.json", "{}") or "{}")
        return data.get("info", {})

    def settings(self) -> Settings:
        data = json.loads(self._read("project.json", "{}") or "{}")
        return Settings.from_dict(data.get("settings", {}))

    def save(self, settings: Settings | None = None, **info) -> None:
        data = json.loads(self._read("project.json", "{}") or "{}")
        data.setdefault("info", {}).update(info)
        data["info"]["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if settings is not None:
            settings.validate()
            data["settings"] = settings.to_dict()
        self._write("project.json", json.dumps(data, indent=2, ensure_ascii=False))

    # --- title list and aliases ------------------------------------------
    def titles(self) -> str:
        return self._read("titles.txt")

    def set_titles(self, text: str) -> None:
        self._write("titles.txt", text)

    def aliases(self) -> str:
        return self._read("aliases.txt")

    def set_aliases(self, text: str) -> None:
        self._write("aliases.txt", text)

    # --- cover you uploaded -------------------------------------------
    @property
    def cover_path(self) -> Path:
        return self.dir / "cover.png"

    def cover(self) -> bytes | None:
        return self.cover_path.read_bytes() if self.cover_path.exists() else None

    def set_cover(self, data: bytes) -> None:
        """Save an uploaded picture as cover.png (any format Pillow reads; shrunk to fit 1000 px)."""
        from PIL import Image
        try:
            im = Image.open(io.BytesIO(data))
            im.load()
        except Exception as exc:
            raise ProjectError("That file is not a picture (use PNG, JPG, WebP or GIF).") from exc
        im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
        im.thumbnail((COVER_MAX, COVER_MAX))
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        self.cover_path.write_bytes(buf.getvalue())

    def remove_cover(self) -> None:
        self.cover_path.unlink(missing_ok=True)

    # --- results -------------------------------------------------------
    def zim_files(self) -> list[Path]:
        if not self.output_dir.exists():
            return []
        return sorted(self.output_dir.glob("*.zim"), key=lambda p: p.stat().st_mtime, reverse=True)

    def summary(self) -> dict:
        """Short description used by project lists (web UI and MCP)."""
        info, s = self.info(), self.settings()
        zims = self.zim_files()
        return {
            "id": self.id,
            "name": s.title or info.get("name") or self.id,
            "original_file": info.get("original_file", ""),
            "created": info.get("created", ""),
            "updated": info.get("updated", ""),
            "strategy": s.strategy,
            "zim": zims[0].name if zims else None,
            "has_cover_upload": self.cover_path.exists(),
            "zim_size": zims[0].stat().st_size if zims else None,
        }


class ProjectStore:
    def __init__(self, config: Config):
        self.config = config
        self.root = config.projects_dir

    def get(self, project_id: str) -> Project:
        if not _ID_OK.match(project_id or ""):
            raise ProjectError(f"'{project_id}' is not a valid project id.")
        d = self.root / project_id
        if not (d / "book.epub").exists():
            raise ProjectError(f"No project called '{project_id}'. Use list_projects to see them.")
        return Project(project_id, d)

    def list(self) -> list[Project]:
        items = [Project(d.name, d) for d in self.root.iterdir() if (d / "book.epub").exists()]
        return sorted(items, key=lambda p: (p.dir / "project.json").stat().st_mtime if (p.dir / "project.json").exists() else 0, reverse=True)

    def create(self, data: bytes, original_name: str) -> Project:
        """New project from the bytes of an EPUB file."""
        if not data[:2] == b"PK":
            raise ProjectError("That file is not an EPUB (EPUB files are zip archives).")
        stem = Path(original_name).stem
        project_id = f"{slugify(stem)}-{secrets.token_hex(3)}"
        d = self.root / project_id
        d.mkdir(parents=True)
        (d / "book.epub").write_bytes(data)
        project = Project(project_id, d)
        project.save(Settings(), name=stem, original_file=Path(original_name).name,
                     created=time.strftime("%Y-%m-%d %H:%M:%S"))
        return project

    def inbox_file(self, file_name: str, suffixes: tuple[str, ...] = (".epub",)) -> Path:
        """A file inside <data>/inbox. Only plain file names are accepted, so nothing
        outside the inbox can be read."""
        if not file_name or Path(file_name).name != file_name:
            raise ProjectError("Give just the file name of a file inside the inbox folder, e.g. 'mybook.epub'.")
        path = self.config.inbox_dir / file_name
        if not path.is_file():
            available = ", ".join(sorted(p.name for p in self.config.inbox_dir.iterdir()
                                         if p.suffix.lower() in suffixes)) or "none"
            raise ProjectError(f"'{file_name}' is not in the inbox. Matching files there: {available}.")
        return path

    def import_from_inbox(self, file_name: str) -> Project:
        """New project from an EPUB already in <data>/inbox (used by MCP and CLI)."""
        return self.create(self.inbox_file(file_name).read_bytes(), file_name)

    def delete(self, project_id: str) -> None:
        project = self.get(project_id)
        shutil.rmtree(project.dir)
