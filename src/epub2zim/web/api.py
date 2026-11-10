"""The REST API used by the web UI (and handy for scripts).

All routes live under /api. Documentation: docs/api.md, or open /api/docs
in a browser for the interactive version FastAPI generates.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .. import __version__, pipeline
from ..config import Config
from ..projects import ProjectStore
from ..settings import Settings
from ..titlelist import TitleListError, parse, parse_aliases


class TextBody(BaseModel):
    text: str = ""


class SuggestBody(BaseModel):
    method: str = "toc"
    level: int = 2
    pattern: str = ""


def create_router(config: Config, store: ProjectStore) -> APIRouter:
    r = APIRouter(prefix="/api")

    def base_url(request: Request) -> str:
        return str(request.base_url).rstrip("/")

    # ---------------------------------------------------------------- general
    @r.get("/health")
    def health():
        return {"ok": True, "version": __version__}

    @r.get("/config")
    def get_config(request: Request):
        """Settings shown on the Settings page (the key itself is not included)."""
        return {
            "version": __version__, "port": config.port, "host": config.host,
            "data_dir": str(config.data_dir), "inbox_dir": str(config.inbox_dir),
            "output_dir": str(config.output_dir), "max_upload_mb": config.max_upload_mb,
            "mcp_url": base_url(request) + "/mcp", "mcp_auth": config.mcp_auth,
            "mcp_key_source": config.mcp_key_source,
            "mcp_key_hint": (config.mcp_key or "")[:6] + "…",
        }

    @r.get("/config/mcp-key")
    def reveal_key():
        """The full MCP key, for the 'Show key' button (the UI is meant for your own computer)."""
        return {"key": config.mcp_key}

    # ---------------------------------------------------------------- projects
    @r.get("/projects")
    def list_projects():
        return [p.summary() for p in store.list()]

    @r.post("/projects")
    async def upload(file: UploadFile = File(...)):
        limit = config.max_upload_mb * 1024 * 1024
        data = await file.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"The file is larger than {config.max_upload_mb} MB (EPUB2ZIM_MAX_UPLOAD_MB).")
        project = store.create(data, file.filename or "book.epub")
        try:
            project.save(pipeline.default_settings_from_book(project))
        except ValueError:
            store.delete(project.id)
            raise
        return project.summary()

    @r.get("/projects/{pid}")
    def get_project(pid: str):
        p = store.get(pid)
        return {"summary": p.summary(), "settings": p.settings().to_dict(), "titles": p.titles(),
                "aliases": p.aliases(), "inspect": pipeline.inspect_book(p.epub_path),
                "zims": [{"name": z.name, "size": z.stat().st_size} for z in p.zim_files()]}

    @r.delete("/projects/{pid}")
    def delete_project(pid: str):
        store.delete(pid)
        return {"deleted": pid}

    @r.put("/projects/{pid}/settings")
    def save_settings(pid: str, body: dict):
        p = store.get(pid)
        s = Settings.from_dict({**p.settings().to_dict(), **body})
        p.save(s, name=s.title or p.info().get("name", pid))
        return s.to_dict()

    @r.put("/projects/{pid}/titles")
    def save_titles(pid: str, body: TextBody):
        entries = parse(body.text)                      # raises a friendly error on bad lines
        store.get(pid).set_titles(body.text)
        return {"articles": len([e for e in entries if not e.is_group])}

    @r.put("/projects/{pid}/aliases")
    def save_aliases(pid: str, body: TextBody):
        n = len(parse_aliases(body.text))
        store.get(pid).set_aliases(body.text)
        return {"aliases": n}

    # ---------------------------------------------------------------- looking inside
    @r.get("/projects/{pid}/pages")
    def pages(pid: str, start: int = 1, count: int = 3, chars: int = 600):
        return pipeline.sample_pages(store.get(pid).epub_path, start, count, min(chars, 5000))

    @r.get("/projects/{pid}/find")
    def find(pid: str, q: str, regex: bool = False, limit: int = 30):
        return pipeline.find_text(store.get(pid).epub_path, q, regex, min(limit, 200))

    @r.post("/projects/{pid}/suggest")
    def suggest(pid: str, body: SuggestBody):
        return {"text": pipeline.suggest_titles(store.get(pid).epub_path, body.method, body.level, body.pattern)}

    # ---------------------------------------------------------------- results
    @r.post("/projects/{pid}/preview")
    def preview(pid: str):
        p = store.get(pid)
        return pipeline.preview(p.epub_path, p.settings(), p.titles())

    @r.post("/projects/{pid}/build")
    def build(pid: str):
        report = pipeline.build_project(store.get(pid), config.output_dir)
        report.pop("file", None)                         # don't expose server paths
        return report

    @r.get("/projects/{pid}/download/{file_name}")
    def download(pid: str, file_name: str):
        p = store.get(pid)
        match = next((z for z in p.zim_files() if z.name == file_name), None)
        if not match:
            raise HTTPException(404, "No such file. Build the ZIM first.")
        return FileResponse(match, media_type="application/octet-stream", filename=match.name)

    return r


def friendly_errors(app) -> None:
    """Turn our errors into {"detail": "..."} with a sensible status code."""
    from fastapi.responses import JSONResponse

    from ..projects import ProjectError

    @app.exception_handler(ProjectError)
    async def _project(_, exc):
        return JSONResponse({"detail": str(exc)}, status_code=404 if "No project" in str(exc) else 400)

    @app.exception_handler(TitleListError)
    async def _titles(_, exc):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.exception_handler(ValueError)
    async def _value(_, exc):
        return JSONResponse({"detail": str(exc)}, status_code=400)
