"""Puts the pieces together into one web application.

    /          the web UI (static files in web/static)
    /api/...   the REST API (api.py)
    /mcp       the MCP server for AI assistants (mcp_server.py), protected by the MCP key
"""

from __future__ import annotations

import contextlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from mcp.server.transport_security import TransportSecuritySettings

from .. import __version__
from ..config import Config
from ..mcp_server import BearerAuth, create_mcp
from ..projects import ProjectStore
from .api import create_router, friendly_errors

STATIC_DIR = Path(__file__).parent / "static"


def create_app(config: Config | None = None):
    config = (config or Config()).prepare()
    store = ProjectStore(config)

    # MCP over "Streamable HTTP". DNS-rebinding protection is off because clients
    # reach us under many host names (localhost, host.docker.internal, a LAN IP);
    # the Bearer key check below is what protects the endpoint.
    mcp = create_mcp(config, store)
    mcp_http = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    mcp_guarded = BearerAuth(mcp_http, config.mcp_key, enabled=config.mcp_auth)

    @contextlib.asynccontextmanager
    async def lifespan(_app):
        # The MCP app needs its own background task group while the server runs.
        async with mcp_http.router.lifespan_context(mcp_http):
            yield

    api = FastAPI(title="epub2zim", version=__version__, lifespan=lifespan,
                  docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
    api.include_router(create_router(config, store))
    friendly_errors(api)
    api.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
    api.state.config = config

    async def app(scope, receive, send):
        """Send /mcp requests to the MCP server, everything else to FastAPI."""
        path = scope.get("path", "")
        if scope["type"] == "http" and (path == "/mcp" or path.startswith("/mcp/")):
            if path != "/mcp":                       # accept /mcp/ too
                scope = {**scope, "path": "/mcp"}
            return await mcp_guarded(scope, receive, send)
        return await api(scope, receive, send)

    app.state = api.state      # tests and the CLI can reach the config here
    app.fastapi = api
    return app
