"""The `epub2zim` command.

    epub2zim serve                    start the web UI + MCP server (port 5100)
    epub2zim mcp-stdio                MCP server over stdio (for clients that start it themselves)
    epub2zim inspect BOOK.epub        what kind of book is it?
    epub2zim suggest BOOK.epub        print a suggested title list
    epub2zim preview BOOK.epub        show the articles that would be made
    epub2zim convert BOOK.epub        make the .zim file

Run any command with --help for its options.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__


def _config(args):
    from .config import Config
    cfg = Config()
    if getattr(args, "data_dir", None):
        cfg.data_dir = Path(args.data_dir)
    if getattr(args, "port", None):
        cfg.port = args.port
    if getattr(args, "host", None):
        cfg.host = args.host
    if getattr(args, "mcp_key", None):
        cfg.mcp_key = args.mcp_key
    if getattr(args, "no_mcp_auth", False):
        cfg.mcp_auth = False
    return cfg.prepare()


def _settings(args):
    from .settings import Settings
    data = {k: v for k, v in {
        "strategy": args.strategy, "heading_level": args.heading_level, "title": args.title,
        "language": args.language, "description": args.description, "creator": args.creator,
        "page_offset": args.page_offset,
    }.items() if v is not None}
    if args.subheading:
        data["subheadings"] = args.subheading
    if args.lists:
        data["detect_lists"] = True
    if args.no_links:
        data["autolink"] = False
    return Settings.from_dict(data)


def _read(path):
    return Path(path).read_text(encoding="utf-8") if path else ""


def cmd_serve(args) -> None:
    import uvicorn
    from .web import create_app
    cfg = _config(args)
    app = create_app(cfg)
    shown = "localhost" if cfg.host in ("0.0.0.0", "127.0.0.1") else cfg.host
    print(f"✿ epub2zim {__version__}")
    print(f"  Web UI:      http://{shown}:{cfg.port}/")
    print(f"  MCP server:  http://{shown}:{cfg.port}/mcp   (key: {'off' if not cfg.mcp_auth else cfg.mcp_key_source})")
    print(f"  Data folder: {cfg.data_dir}")
    uvicorn.run(app, host=cfg.host, port=cfg.port, log_level="warning")


def cmd_mcp_stdio(args) -> None:
    from .mcp_server import create_mcp
    from .projects import ProjectStore
    cfg = _config(args)
    create_mcp(cfg, ProjectStore(cfg)).run("stdio")


def cmd_inspect(args) -> None:
    from .pipeline import inspect_book
    print(json.dumps(inspect_book(args.epub), indent=2, ensure_ascii=False))


def cmd_suggest(args) -> None:
    from .pipeline import suggest_titles
    print(suggest_titles(args.epub, args.method, args.level, args.pattern or ""), end="")


def cmd_preview(args) -> None:
    from .pipeline import preview
    pv = preview(args.epub, _settings(args), _read(args.titles))
    print(f"{pv['article_count']} articles (strategy: {pv['strategy']}, page offset: {pv['page_offset']})")
    for m in pv["misses"]:
        print(f"  NOT FOUND: {m}")
    for w in pv["warnings"]:
        print(f"  warning: {w}")
    for a in pv["articles"]:
        print(f"{a['n']:>4}  {'  ' * (a['level'] - 1)}{a['title'][:70]:<70} {a['chars']:>8}")


def cmd_convert(args) -> None:
    from .pipeline import build
    out = args.output or Path(args.epub).with_suffix(".zim")
    report = build(args.epub, _settings(args), out, _read(args.titles), _read(args.aliases))
    report.pop("file", None)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"✿ Wrote {out}")


def _split_options(p) -> None:
    p.add_argument("epub", help="the EPUB file")
    p.add_argument("--strategy", choices=["toc", "headings", "files", "titles"], help="how to split (default: toc)")
    p.add_argument("--heading-level", type=int, help="headings strategy: split at h1..hN (default 2)")
    p.add_argument("--titles", help="title list file (for --strategy titles)")
    p.add_argument("--page-offset", help="scanned books: 'auto' (default), a number, or '' for none")
    p.add_argument("--subheading", action="append", help="phrase to turn into a section heading (repeatable)")
    p.add_argument("--lists", action="store_true", help="put 'A. ...' / '1. ...' items on separate lines")
    p.add_argument("--no-links", action="store_true", help="don't link mentions of other article titles")
    p.add_argument("--title", help="title shown in the ZIM reader")
    p.add_argument("--language", help="3-letter language code, e.g. eng")
    p.add_argument("--description", help="one line, max 80 characters")
    p.add_argument("--creator", help="author")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="epub2zim", description="Turn EPUB books into searchable ZIM files.")
    parser.add_argument("--version", action="version", version=f"epub2zim {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, fn, help_text in (("serve", cmd_serve, "start the web UI and MCP server"),
                                ("mcp-stdio", cmd_mcp_stdio, "run the MCP server over stdio")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--data-dir", help="data folder (default ./data or EPUB2ZIM_DATA_DIR)")
        p.add_argument("--mcp-key", help="MCP key (default: EPUB2ZIM_MCP_KEY or a generated one)")
        if name == "serve":
            p.add_argument("--port", type=int, help="port (default 5100 or EPUB2ZIM_PORT)")
            p.add_argument("--host", help="address to listen on (default 127.0.0.1; 0.0.0.0 for all)")
            p.add_argument("--no-mcp-auth", action="store_true", help="switch the MCP key check off (not recommended)")
        p.set_defaults(func=fn)

    p = sub.add_parser("inspect", help="describe a book and suggest a strategy")
    p.add_argument("epub")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("suggest", help="print a suggested title list")
    p.add_argument("epub")
    p.add_argument("--method", default="toc", choices=["toc", "headings", "running_headers", "pattern"])
    p.add_argument("--level", type=int, default=2)
    p.add_argument("--pattern", help="regular expression with one (group) for --method pattern")
    p.set_defaults(func=cmd_suggest)

    p = sub.add_parser("preview", help="show the articles that would be made")
    _split_options(p)
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("convert", help="make the .zim file")
    _split_options(p)
    p.add_argument("-o", "--output", help="output .zim path (default: next to the EPUB)")
    p.add_argument("--aliases", help="aliases file ('Short name = Article title' per line)")
    p.set_defaults(func=cmd_convert)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
