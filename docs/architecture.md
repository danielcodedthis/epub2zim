# Architecture: which file does what

epub2zim is a set of small modules, each with one job and comments at the top explaining
it. Read [How it works](how-it-works.md) first for the big picture.

## Python package (`src/epub2zim/`)

| File | Job | Change it to… |
|---|---|---|
| `config.py` | Environment variables / flags → `Config` | add a server setting |
| `settings.py` | Per-book settings (`Settings`) | add a per-book option |
| `epub_reader.py` | EPUB zip → `Book` (metadata, spine, TOC, images) | support odd EPUBs |
| `blocks.py` | Chapter HTML → `Block`s | change what counts as a paragraph/block |
| `cleaning.py` | Scanned pages → clean text, page offset | handle another scan format |
| `titlelist.py` | Title list & alias text formats | extend the format |
| `splitters/` | The four strategies (one file each) + `base.py` | add a strategy |
| `propose.py` | Automatic title lists | add a “Fill from” method |
| `article_edits.py` | After splitting: renames, part names in front of short titles, leaving articles out | change title rules |
| `formatter.py` | Article content → safe HTML | allow more tags, change paragraphs |
| `autolink.py` | Wiki-style links | change linking rules |
| `zim_pages.py` | Article/home page HTML and CSS inside the ZIM | change how articles look |
| `zim_writer.py` | libzim, icon, metadata | change ZIM metadata |
| `projects.py` | Data folder: one folder per book | change storage |
| `pipeline.py` | The steps everyone calls: inspect, sample, find, suggest, preview, build | add a step |
| `web/api.py` | REST routes | add an endpoint |
| `web/app.py` | Joins API, UI and MCP; routes `/mcp` through the key check | change mounting |
| `mcp_server.py` | MCP tools, workflow text, Bearer key check | add/change a tool |
| `cli.py` | The `epub2zim` command | add a command/flag |

Dependencies point one way: `pipeline` uses the modules above it; `web`, `mcp_server` and
`cli` only use `pipeline`, `projects`, `settings` and `titlelist`. Nothing imports `web`.

## Web UI (`src/epub2zim/web/static/`)

No build step: plain HTML, CSS and JavaScript modules. Edit and reload.

```
index.html                  page frame: top bar, decoration, <main id="view">
css/base.css                fonts + Blush colour tokens
css/themes.css              Midnight (dark) theme
css/decor.css               background blobs and sparkles
css/layout.css              top bar, page, cards
css/components/*.css        buttons, forms, chips, dialog, toast, cards
css/pages.css               steps, guide boxes, tables, snippets
js/app.js                   router (#/, #/book/<id>, #/help, #/settings)
js/api.js                   all calls to the REST API
js/dom.js                   helpers: esc(), el(), bytes(), debounce(), copyText()
js/components/              toast, confirm dialog, theme switch
js/pages/home.js            start page: upload + book list
js/pages/project/index.js   one book: the five steps and auto-saving
js/pages/project/look.js    step 1     split.js  step 2     details.js  step 3
js/pages/project/preview.js step 4     build.js  step 5
js/pages/help.js            quick guide
js/pages/settings.js        storage, MCP setup snippets, theme
fonts/                      Nunito + Quicksand (SIL OFL), bundled: no internet needed
```

### Design rules (Blush)

- Components use **tokens** (`--surface`, `--text`, `--accent`, `--ok`…), never raw
  colours, so the Midnight theme works automatically.
- **One gradient button per view** (`.primary-btn`): *Build ZIM file*. Everything else is
  `.pill-btn` / `.link-btn`.
- **Destructive actions are quiet and far away:** `.danger-link` at the bottom, always
  behind `confirmBox()` with focus on Cancel.
- Rounded everything; pink-tinted shadows; decoration stays behind content.
- Check both themes and a 390 px wide phone screen after changes.

## Adding a splitting strategy

1. Write `splitters/mystrategy.py` with a function returning `SplitResult(articles=[…])`.
   Build articles with `blocks_to_article()` (HTML) or `Article(..., kind="text")`.
2. Add `"mystrategy"` to `STRATEGIES` in `settings.py`.
3. Add a branch in `splitters/__init__.py: split()`.
4. Add a card to `CHOICES` in `web/static/js/pages/project/split.js`, and the name to
   `cli.py`'s `--strategy` choices.
5. Add a test in `tests/test_splitting.py` and a section in `docs/splitting-strategies.md`.

## Adding an MCP tool

In `create_mcp()` in `mcp_server.py`:

```python
@mcp.tool()
@friendly                      # turns our errors into readable tool errors
def my_tool(project_id: str, n: int = 5) -> str:
    """One or two sentences: the model reads this to decide when to call the tool."""
    return "short plain-text answer"
```

Keep answers short, and add the tool to `docs/mcp-server.md` and the skills.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

`tests/epub_factory.py` builds tiny EPUBs on the fly (a normal book and a fake scan), so the
tests need no real books. CI (`.github/workflows/tests.yml`) runs them on Python 3.11–3.13
and checks the Docker image starts.
