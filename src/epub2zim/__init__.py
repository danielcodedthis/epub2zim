"""epub2zim: turn EPUB books into searchable, wiki-style ZIM files.

The package is split into small modules, each doing one job:

    config.py        settings from environment variables / command line
    epub_reader.py   opens an EPUB: metadata, reading order, table of contents, images
    blocks.py        breaks each chapter file into paragraph-sized "blocks"
    cleaning.py      tidies OCR text (page numbers, running headers)
    titlelist.py     reads/writes the plain-text "title list" format
    splitters/       the four ways to cut a book into articles
    propose.py       suggests a title list automatically
    formatter.py     turns an article's content into tidy HTML
    autolink.py      links mentions of other article titles (wiki-style)
    zim_pages.py     the HTML/CSS of pages inside the ZIM file
    zim_writer.py    writes the .zim file itself
    projects.py      keeps each book's files and settings in the data folder
    pipeline.py      the high-level steps used by the web UI, CLI and MCP server
    web/             the web app (API + Blush user interface)
    mcp_server.py    tools for AI assistants (LM Studio, Open WebUI, ...)
    cli.py           the `epub2zim` command
"""

__version__ = "0.1.0"

import warnings as _warnings

# EPUB chapters are XHTML; we parse them with the forgiving HTML parser on purpose.
try:
    from bs4 import XMLParsedAsHTMLWarning as _XmlWarning
    _warnings.filterwarnings("ignore", category=_XmlWarning)
except ImportError:  # very old BeautifulSoup
    pass
