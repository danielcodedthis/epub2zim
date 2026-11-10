"""Per-book settings: everything the user can choose for one conversion.

They are stored as project.json in the book's project folder and edited in the
web UI (step 3), with `update_settings` over MCP, or with CLI flags.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields

STRATEGIES = ("toc", "headings", "files", "titles")


@dataclass
class Settings:
    # --- About the ZIM file (shown in your ZIM reader's library) ---
    title: str = ""              # e.g. "Moby-Dick"
    description: str = ""        # one line, max 80 characters
    language: str = "eng"        # ISO 639-3 code: eng, deu, fra, spa, bul, ...
    creator: str = ""            # author
    publisher: str = "epub2zim"
    name: str = ""               # short machine name, e.g. "moby_dick_en"; made from the title if empty

    # --- How to split the book into articles ---
    strategy: str = "toc"        # toc | headings | files | titles (see docs/splitting-strategies.md)
    heading_level: int = 2       # "headings" strategy: split at <h1> .. <hN>

    # --- Scanned (OCR) books, used by the "titles" strategy ---
    clean_text: bool = True      # remove printed page numbers and running headers
    page_offset: str = "auto"    # "auto", a number, or "" for none
    subheadings: list[str] = field(default_factory=list)  # phrases to turn into section headings
    detect_lists: bool = False   # turn "A. ... B. ..." and "1. ... 2. ..." into separate lines
    paragraph_size: int = 650    # rough paragraph length (characters) when the scan lost paragraphs

    # --- Extras ---
    autolink: bool = True        # link mentions of other article titles, like a wiki
    autolink_min_length: int = 8 # ignore titles shorter than this (avoids silly links)
    include_images: bool = True  # copy the book's pictures into the ZIM

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        """Build Settings from a dict, ignoring unknown keys and fixing types."""
        known = {f.name: f for f in fields(cls)}
        clean = {}
        for key, value in (data or {}).items():
            if key not in known:
                continue
            default = getattr(cls(), key)
            if isinstance(default, bool):
                value = value if isinstance(value, bool) else str(value).lower() in ("1", "true", "yes", "on")
            elif isinstance(default, int):
                value = int(value)
            elif isinstance(default, list):
                if isinstance(value, str):
                    value = [v.strip() for v in value.splitlines() if v.strip()]
                value = [str(v) for v in value]
            else:
                value = "" if value is None else str(value)
            clean[key] = value
        s = cls(**clean)
        s.validate()
        return s

    def validate(self) -> None:
        if self.strategy not in STRATEGIES:
            raise ValueError(f"strategy must be one of {', '.join(STRATEGIES)}")
        if not 1 <= self.heading_level <= 6:
            raise ValueError("heading_level must be between 1 and 6")
        if len(self.description) > 80:
            raise ValueError("description must be 80 characters or fewer (a ZIM file rule)")
        if self.paragraph_size < 200:
            raise ValueError("paragraph_size must be at least 200")
