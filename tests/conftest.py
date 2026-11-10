"""Shared test fixtures: small generated EPUBs and a web app with a temporary data folder."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))   # so tests can import epub_factory

from epub_factory import make_epub, make_scanned_epub  # noqa: E402


@pytest.fixture
def book(tmp_path) -> Path:
    """A normal EPUB 3 book with a nav table of contents."""
    return make_epub(tmp_path / "harbour.epub", toc="nav")


@pytest.fixture
def book_ncx(tmp_path) -> Path:
    return make_epub(tmp_path / "harbour-ncx.epub", toc="ncx")


@pytest.fixture
def book_no_toc(tmp_path) -> Path:
    return make_epub(tmp_path / "harbour-notoc.epub", toc="none")


@pytest.fixture
def scanned(tmp_path) -> Path:
    """A fake scanned book: one file per printed page, page numbers and running headers."""
    return make_scanned_epub(tmp_path / "garden-scan.epub")


@pytest.fixture
def config(tmp_path):
    from epub2zim.config import Config
    return Config(data_dir=tmp_path / "data", mcp_key="test-key-123").prepare()


@pytest.fixture
def client(config):
    from fastapi.testclient import TestClient
    from epub2zim.web import create_app
    with TestClient(create_app(config)) as c:
        yield c
