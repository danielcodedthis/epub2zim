# Getting started

You can run epub2zim with **Docker** (recommended) or install it with **pip**.

## Option A: Docker (recommended)

You need [Docker](https://docs.docker.com/get-docker/) (Docker Desktop on Windows/macOS).

```bash
git clone https://github.com/danielcodedthis/epub2zim.git
cd epub2zim
docker compose up -d
```

Open **http://localhost:5100**. Your books and finished ZIM files are kept in the `data`
folder next to `docker-compose.yml`.

To stop it: `docker compose down`. To update: `git pull && docker compose up -d --build`.

More options in [Docker](docker.md).

## Option B: pip

You need Python 3.10 or newer.

```bash
git clone https://github.com/danielcodedthis/epub2zim.git
cd epub2zim
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install .
epub2zim serve
```

Open **http://localhost:5100**. Data goes into `./data` (change with `--data-dir`).

## Your first book

1. **Drop an EPUB** onto the start page.
2. **Step 1 – Look at the book.** epub2zim tells you what it found and suggests a strategy.
3. **Step 2 – Choose how to split.** For most books keep the suggestion (*Table of contents*).
4. **Step 3 – Name & extras.** Check the title and language.
5. **Step 4 – Preview.** See every article that will be made. Nothing is written yet.
6. **Step 5 – Build.** Click **Build ZIM file**, then **Download**.

Open the file in your ZIM reader. Zimi and kiwix-serve can also watch the
`data/output` folder, where every finished ZIM is copied.

## Without the web page

```bash
epub2zim convert mybook.epub                       # writes mybook.zim
epub2zim convert mybook.epub --strategy headings   # split at headings instead
```

See [Command line](cli.md).

## Next

- A scanned book? Read the [scanned books walkthrough](scanned-books.md).
- Want an AI assistant to do it? See [MCP server](mcp-server.md).
