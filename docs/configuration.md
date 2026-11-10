# Configuration

Everything is set with **environment variables** or **command-line flags**. Flags win.
The code is in [`src/epub2zim/config.py`](../src/epub2zim/config.py).

| Environment variable | Flag (`epub2zim serve …`) | Default | What it does |
|---|---|---|---|
| `EPUB2ZIM_DATA_DIR` | `--data-dir` | `./data` (`/data` in Docker) | Where books, settings and ZIM files are kept |
| `EPUB2ZIM_PORT` | `--port` | `5100` | Port for the web UI, API and MCP server |
| `EPUB2ZIM_HOST` | `--host` | `127.0.0.1` (`0.0.0.0` in Docker) | Network address to listen on. `0.0.0.0` = all |
| `EPUB2ZIM_MCP_KEY` | `--mcp-key` | generated | Key AI assistants must send |
| `EPUB2ZIM_MCP_AUTH` | `--no-mcp-auth` | `on` | Switch the key check off |
| `EPUB2ZIM_MAX_UPLOAD_MB` | | `300` | Largest EPUB upload in the web UI |

Docker-only: `PUID` and `PGID` (default 1000) set the owner of the data files.
In docker compose, `EPUB2ZIM_DATA` picks the folder on your computer.

## The MCP key

AI assistants must send the key with every request, as

```
Authorization: Bearer <key>
```

(`X-API-Key: <key>` also works.)

- **Not set:** a random key (`e2z_…`) is made on first start and saved as
  `<data>/mcp_key.txt`, so it stays the same after restarts. The **Settings** page shows it
  (click *Show*).
- **Set it yourself:** `EPUB2ZIM_MCP_KEY=some-long-random-text`. A good way to make one:
  `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- **New key:** delete `mcp_key.txt` and restart (or change the variable). Update your
  assistants afterwards.
- **No key at all:** `EPUB2ZIM_MCP_AUTH=off`. Only do this if nothing else can reach the port.

The `mcp-stdio` mode (the assistant starts epub2zim itself) needs no key.

## Listening address

On a normal install epub2zim listens on `127.0.0.1`: only your own computer can open it.
To use it from your phone or another computer on your network, start it with
`--host 0.0.0.0` (Docker does this already), then open `http://<your computer's IP>:5100`.

## Per-book settings

The settings of each book (strategy, title, language, …) are not environment variables:
they are chosen in the web UI and stored in `data/projects/<id>/project.json`. All of them
are described in [`settings.py`](../src/epub2zim/settings.py) and in
[Splitting strategies](splitting-strategies.md) / [Aliases and extras](aliases-and-extras.md).
