"""MCP server: lets AI assistants (LM Studio, Open WebUI, Claude Desktop, ...) use epub2zim.

Two ways to connect:
  * Streamable HTTP at  http://<host>:<port>/mcp   (needs the MCP key as a Bearer token)
  * stdio:  `epub2zim mcp-stdio`                     (the client starts the process itself)

Tool answers are short plain text on purpose: small local models have small
context windows, so every tool returns only what is needed for the next step.
The workflow the tools are designed for is in WORKFLOW below (and in
docs/mcp-server.md and skills/).
"""

from __future__ import annotations

import functools
import hmac
import json

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import __version__, pipeline
from .config import Config
from .projects import ProjectError, ProjectStore
from .settings import STRATEGIES, Settings
from .titlelist import TitleListError, parse, parse_aliases

WORKFLOW = """epub2zim turns an EPUB book into a ZIM file (an offline, searchable mini-wiki).
Steps:
1. list_inbox, then import_epub(file_name)  -> gives a project_id and a first look at the book.
   (Or list_projects to continue an existing project.)
2. inspect_book: read 'suggested_strategy' and 'reason'.
   - toc: the book's own table of contents (normal EPUBs). Usually just preview and build.
   - headings: split at <h1>..<hN>; set heading_level.
   - files: one article per file (fallback).
   - titles: scanned/OCR books. You need a title list (step 3).
3. For 'titles': suggest_titles(method='running_headers' or 'pattern'), check with read_pages/find_text,
   fix the list with set_title_list or replace_in_title_list. Format: 'Title | page | text to look for',
   '-' prefix per nesting level, '= Group' for headings on the home page.
4. update_settings: title, description (<=80 chars; always set one), language (3 letters, e.g. eng), creator.
5. preview_split: look at article count, 'misses' (titles not found) and tiny/huge articles. Fix and repeat.
   - Junk articles (title page, credits, contents): update_settings {"exclude": ["Title page", "Credits*"]}.
   - Chapters only called I, II, 3...: parent_prefix "short" (default) makes them "Part One · I".
   - Other bad titles: update_settings {"renames": ["Old title = New title"]}.
6. Optional: set_aliases ('Short name = Article title' per line), set_cover(file_name from the inbox).
7. build_zim -> file name and download link. Tell the user where the file is.
Ask the user before overwriting a title list they wrote themselves, and before delete_project."""


def friendly(fn):
    """Turn our expected errors into tool errors the model can read and act on
    (instead of a generic "unexpected exception")."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (ProjectError, TitleListError, ValueError, FileNotFoundError) as exc:
            raise ToolError(str(exc)) from exc
    return wrapper


def _fmt(data) -> str:
    """Compact JSON for structured answers."""
    return json.dumps(data, ensure_ascii=False, indent=1)


def create_mcp(config: Config, store: ProjectStore) -> MCPServer:
    mcp = MCPServer(name="epub2zim", version=__version__, instructions=WORKFLOW, log_level="WARNING",
                    description="Convert EPUB books into searchable ZIM files.")

    def project(pid: str):
        return store.get(pid)

    @mcp.tool()
    @friendly
    def how_it_works() -> str:
        """Explains the conversion workflow and which tool to use when. Call this first if unsure."""
        return WORKFLOW

    @mcp.tool()
    @friendly
    def list_projects() -> str:
        """Lists existing book projects (id, name, strategy, last built ZIM)."""
        items = [p.summary() for p in store.list()]
        if not items:
            return "No projects yet. Put an EPUB in the inbox folder and call import_epub, or upload one in the web UI."
        return "\n".join(f"{i['id']} | {i['name']} | strategy={i['strategy']} | zim={i['zim'] or '-'}" for i in items)

    @mcp.tool()
    @friendly
    def list_inbox() -> str:
        """Lists EPUB files waiting in the data folder's 'inbox' (import them with import_epub)."""
        files = sorted(p.name for p in config.inbox_dir.glob("*.epub"))
        return "\n".join(files) if files else f"The inbox is empty. Copy EPUB files to: {config.inbox_dir}"

    @mcp.tool()
    @friendly
    def import_epub(file_name: str) -> str:
        """Creates a project from an EPUB in the inbox (give just the file name). Returns the project id and a first look."""
        p = store.import_from_inbox(file_name)
        p.save(pipeline.default_settings_from_book(p))
        report = pipeline.inspect_book(p.epub_path)
        return f"project_id: {p.id}\n" + _fmt({k: report[k] for k in (
            "title", "author", "files", "toc_entries", "headings", "looks_scanned", "suggested_strategy", "reason")})

    @mcp.tool()
    @friendly
    def inspect_book(project_id: str) -> str:
        """Describes the book: files, table of contents, headings, scanned or not, and the suggested strategy."""
        return _fmt(pipeline.inspect_book(project(project_id).epub_path))

    @mcp.tool()
    @friendly
    def read_pages(project_id: str, start_page: int = 1, count: int = 3, chars: int = 400) -> str:
        """Shows the plain text of a few page files (count max 20, text cut to `chars` each)."""
        pages = pipeline.sample_pages(project(project_id).epub_path, start_page, count, min(chars, 3000))
        return "\n\n".join(f"[page {p['page']}, {p['chars']} chars] {p['text']}" for p in pages) or "No such pages."

    @mcp.tool()
    @friendly
    def find_text(project_id: str, query: str, regex: bool = False, limit: int = 15) -> str:
        """Finds pages containing `query` (plain text, or a Python regular expression if regex=true)."""
        hits = pipeline.find_text(project(project_id).epub_path, query, regex, min(limit, 50))
        return "\n".join(f"page {h['page']}: {h['snippet']}" for h in hits) or "Not found."

    @mcp.tool()
    @friendly
    def suggest_titles(project_id: str, method: str, level: int = 2, pattern: str = "", save: bool = False) -> str:
        """Makes a title list automatically. method: toc | headings | running_headers | pattern.
        pattern = regex with one (group) for the title. save=true stores it as the project's title list."""
        p = project(project_id)
        text = pipeline.suggest_titles(p.epub_path, method, level, pattern)
        if save:
            p.set_titles(text)
        lines = text.splitlines()
        shown = "\n".join(lines[:120]) + (f"\n... ({len(lines) - 120} more lines)" if len(lines) > 120 else "")
        return ("Saved as the title list.\n" if save else "Not saved (use save=true or set_title_list).\n") + shown

    @mcp.tool()
    @friendly
    def get_title_list(project_id: str, start_line: int = 1, max_lines: int = 150) -> str:
        """Shows the project's title list (with line numbers)."""
        lines = project(project_id).titles().splitlines()
        part = lines[start_line - 1:start_line - 1 + max_lines]
        if not part:
            return "The title list is empty." if not lines else "No lines in that range."
        return "\n".join(f"{start_line + i}: {l}" for i, l in enumerate(part)) + f"\n(total {len(lines)} lines)"

    @mcp.tool()
    @friendly
    def set_title_list(project_id: str, text: str) -> str:
        """Replaces the whole title list. One entry per line: '- Title | page | text to look for'."""
        try:
            n = len([e for e in parse(text) if not e.is_group])
        except TitleListError as exc:
            return f"Not saved: {exc}"
        project(project_id).set_titles(text)
        return f"Saved. {n} articles in the list."

    @mcp.tool()
    @friendly
    def replace_in_title_list(project_id: str, old: str, new: str) -> str:
        """Small edit: replaces the first occurrence of `old` with `new` in the title list (use new='' to delete)."""
        p = project(project_id)
        text = p.titles()
        if old not in text:
            return "Not found. Use get_title_list to see the exact text."
        text = text.replace(old, new, 1)
        try:
            parse(text)
        except TitleListError as exc:
            return f"Not saved: {exc}"
        p.set_titles(text)
        return "Done."

    @mcp.tool()
    @friendly
    def get_settings(project_id: str) -> str:
        """Shows the project's settings (title, language, strategy, options)."""
        return _fmt(project(project_id).settings().to_dict())

    @mcp.tool()
    @friendly
    def update_settings(project_id: str, changes: dict) -> str:
        """Changes settings, e.g. {"strategy": "headings", "heading_level": 2, "title": "My Book",
        "description": "...", "exclude": ["Title page", "Credits"], "renames": ["Old = New"],
        "parent_prefix": "short"}. strategy: toc | headings | files | titles.
        exclude: titles to leave out (* = wildcard). parent_prefix: never | short | always."""
        p = project(project_id)
        merged = {**p.settings().to_dict(), **(changes or {})}
        try:
            s = Settings.from_dict(merged)
        except (ValueError, TypeError) as exc:
            return f"Not saved: {exc}. Valid strategies: {', '.join(STRATEGIES)}"
        p.save(s)
        return "Saved: " + ", ".join(f"{k}={merged[k]!r}" for k in (changes or {}) if k in s.to_dict())

    @mcp.tool()
    @friendly
    def get_aliases(project_id: str) -> str:
        """Shows the aliases (extra search names) of the project."""
        return project(project_id).aliases() or "No aliases yet."

    @mcp.tool()
    @friendly
    def set_aliases(project_id: str, text: str) -> str:
        """Replaces the aliases: one 'Short name = Article title' per line (e.g. 'PTSD = Posttraumatic Stress Disorder')."""
        try:
            n = len(parse_aliases(text))
        except TitleListError as exc:
            return f"Not saved: {exc}"
        project(project_id).set_aliases(text)
        return f"Saved {n} aliases."

    @mcp.tool()
    @friendly
    def preview_split(project_id: str, first: int = 1, show: int = 40) -> str:
        """Splits the book without building. Shows article count, misses (titles not found),
        warnings, and a slice of the article list: n | level | title | page | characters | first words."""
        p = project(project_id)
        pv = pipeline.preview(p.epub_path, p.settings(), p.titles())
        lines = [f"strategy={pv['strategy']} articles={pv['article_count']} page_offset={pv['page_offset']}"]
        if pv["misses"]:
            lines.append(f"MISSES ({len(pv['misses'])}): " + "; ".join(pv["misses"][:30]))
        lines += [f"WARNING: {w}" for w in pv["warnings"][:10]]
        if pv["excluded"]:
            lines.append(f"LEFT OUT ({len(pv['excluded'])}): " + "; ".join(pv["excluded"][:30]))
        arts = pv["articles"][max(0, first - 1):max(0, first - 1) + min(show, 200)]
        lines += [f"{a['n']} | L{a['level']} | {a['title']} | p{a['page']} | {a['chars']} | {a['start'][:60]}" for a in arts]
        if pv["article_count"] > first - 1 + len(arts):
            lines.append(f"... use first={first + len(arts)} to see more")
        return "\n".join(lines)

    @mcp.tool()
    @friendly
    def set_cover(project_id: str, file_name: str = "") -> str:
        """Uses a picture from the inbox (PNG/JPG/WebP, e.g. 500x500) as the ZIM's cover and icon.
        Give just the file name. Empty file_name removes your cover (the book's own cover is used again)."""
        p = project(project_id)
        if not file_name:
            p.remove_cover()
            return "Cover removed. The book's own cover (if any) will be used."
        p.set_cover(store.inbox_file(file_name, (".png", ".jpg", ".jpeg", ".webp", ".gif")).read_bytes())
        return "Cover saved. It will be the library icon and appear on the home page."

    @mcp.tool()
    @friendly
    def delete_project(project_id: str, confirm: bool = False) -> str:
        """Deletes a project: its EPUB copy, settings, title list and built ZIM files (copies in the
        output folder stay). Ask the user first, then call with confirm=true."""
        p = project(project_id)
        if not confirm:
            return (f"This will delete '{p.summary()['name']}' ({project_id}) and its ZIM files. "
                    "Ask the user, then call delete_project again with confirm=true.")
        store.delete(project_id)
        return f"Deleted {project_id}."

    @mcp.tool()
    @friendly
    def build_zim(project_id: str) -> str:
        """Builds the .zim file (may take a while for big books). Returns the file name and a download link."""
        p = project(project_id)
        report = pipeline.build_project(p, config.output_dir)
        url = f"http://{'localhost' if config.host in ('0.0.0.0', '127.0.0.1') else config.host}:{config.port}" \
              f"/api/projects/{p.id}/download/{report['file_name']}"
        return _fmt({**{k: report[k] for k in ("file_name", "size_bytes", "articles", "aliases", "images",
                                                "misses", "alias_misses", "excluded", "warnings", "seconds")},
                     "download": url, "library_copy": report.get("library_copy")})

    return mcp


class BearerAuth:
    """ASGI wrapper: only lets requests through that carry the right MCP key.

    Accepted forms:  "Authorization: Bearer <key>"  or  "X-API-Key: <key>".
    """

    def __init__(self, app, key: str | None, enabled: bool = True):
        self.app, self.key, self.enabled = app, key or "", enabled

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not self.enabled:
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        given = headers.get("x-api-key", "")
        auth = headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            given = auth[7:].strip()
        if self.key and given and hmac.compare_digest(given, self.key):
            return await self.app(scope, receive, send)
        body = b'{"error":"Missing or wrong MCP key. Send it as: Authorization: Bearer <key>"}'
        await send({"type": "http.response.start", "status": 401,
                    "headers": [(b"content-type", b"application/json"), (b"www-authenticate", b"Bearer")]})
        await send({"type": "http.response.body", "body": body})
