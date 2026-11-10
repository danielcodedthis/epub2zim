"""Settings for the whole app.

Every setting can come from an environment variable (handy in Docker) or from a
command-line flag (see cli.py). Command-line flags win over environment variables.

    EPUB2ZIM_DATA_DIR      where books, settings and finished .zim files are kept   (default: ./data)
    EPUB2ZIM_HOST          network address to listen on                             (default: 127.0.0.1)
    EPUB2ZIM_PORT          port for the web UI and the MCP server                   (default: 5100)
    EPUB2ZIM_MCP_KEY       secret key AI tools must send to use the MCP server      (default: generated)
    EPUB2ZIM_MCP_AUTH      "on" (default) or "off" to switch the key check off
    EPUB2ZIM_MAX_UPLOAD_MB largest EPUB the web UI accepts, in megabytes            (default: 300)
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PORT = 5100
KEY_FILE_NAME = "mcp_key.txt"


def _env(name: str, default: str | None = None) -> str | None:
    """Read an environment variable; treat an empty value as 'not set'."""
    value = os.environ.get(name, "").strip()
    return value or default


@dataclass
class Config:
    data_dir: Path = field(default_factory=lambda: Path(_env("EPUB2ZIM_DATA_DIR", "./data")))
    host: str = field(default_factory=lambda: _env("EPUB2ZIM_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(_env("EPUB2ZIM_PORT", str(DEFAULT_PORT))))
    mcp_key: str | None = field(default_factory=lambda: _env("EPUB2ZIM_MCP_KEY"))
    mcp_auth: bool = field(default_factory=lambda: _env("EPUB2ZIM_MCP_AUTH", "on").lower() not in ("off", "0", "false", "no"))
    max_upload_mb: int = field(default_factory=lambda: int(_env("EPUB2ZIM_MAX_UPLOAD_MB", "300")))

    # Where the key came from: "environment", "file" or "generated" (shown in the UI).
    mcp_key_source: str = "environment"

    def prepare(self) -> "Config":
        """Create the data folders and make sure an MCP key exists. Returns self."""
        self.data_dir = Path(self.data_dir).expanduser().resolve()
        for sub in ("projects", "inbox", "output"):
            (self.data_dir / sub).mkdir(parents=True, exist_ok=True)
        if self.mcp_key:
            self.mcp_key_source = "environment"
        else:
            self.mcp_key, self.mcp_key_source = self._load_or_create_key()
        return self

    def _load_or_create_key(self) -> tuple[str, str]:
        """Keep one random key in <data>/mcp_key.txt so it survives restarts."""
        key_file = self.data_dir / KEY_FILE_NAME
        if key_file.exists() and key_file.read_text().strip():
            return key_file.read_text().strip(), "file"
        key = "e2z_" + secrets.token_urlsafe(24)
        key_file.write_text(key + "\n")
        try:
            key_file.chmod(0o600)  # readable only by the owner
        except OSError:
            pass
        return key, "generated"

    # Handy folder shortcuts -------------------------------------------------
    @property
    def projects_dir(self) -> Path:
        return self.data_dir / "projects"

    @property
    def inbox_dir(self) -> Path:
        """Drop EPUB files here so the MCP server / CLI can import them by name."""
        return self.data_dir / "inbox"

    @property
    def output_dir(self) -> Path:
        """Every finished .zim is also copied here (point your ZIM reader at it)."""
        return self.data_dir / "output"
