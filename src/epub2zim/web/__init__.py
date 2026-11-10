"""The web application: REST API (api.py), app assembly (app.py) and the UI (static/)."""

from .app import create_app

__all__ = ["create_app"]
