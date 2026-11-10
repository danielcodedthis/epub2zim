# Docker

The image contains the web UI, the REST API and the MCP server. One port (5100 by default)
serves all three.

## With docker compose (easiest)

```bash
docker compose up -d          # build (first time) and start
docker compose logs -f        # watch the log (Ctrl+C to stop watching)
docker compose down           # stop
```

Settings go in a `.env` file next to `docker-compose.yml`:

```bash
cp .env.example .env
# edit .env, then:
docker compose up -d
```

| Variable | Default | Meaning |
|---|---|---|
| `EPUB2ZIM_PORT` | `5100` | Port on your computer **and** inside the container |
| `EPUB2ZIM_DATA` | `./data` | Folder on your computer for books and ZIM files |
| `EPUB2ZIM_MCP_KEY` | *(generated)* | Key for AI assistants; see [Configuration](configuration.md) |
| `EPUB2ZIM_MCP_AUTH` | `on` | `off` switches the key check off |
| `EPUB2ZIM_MAX_UPLOAD_MB` | `300` | Largest EPUB the web UI accepts |
| `PUID` / `PGID` | `1000` | Owner of the files in the data folder (run `id` to see yours) |

## With plain docker

```bash
docker build -t epub2zim .
docker run -d --name epub2zim \
  -p 5100:5100 \
  -v "$PWD/data:/data" \
  -e EPUB2ZIM_MCP_KEY="choose-a-long-random-key" \
  --restart unless-stopped \
  epub2zim
```

Different port: change both sides **and** the variable, e.g.
`-p 8080:8080 -e EPUB2ZIM_PORT=8080`.

## The data folder

```
data/
├── inbox/        put EPUBs here for AI assistants / the CLI to import by name
├── output/       every finished .zim is copied here: point Zimi or kiwix-serve at it
├── projects/     one folder per book (book.epub, project.json, titles.txt, aliases.txt, output/)
└── mcp_key.txt   the generated MCP key (only if you didn't set EPUB2ZIM_MCP_KEY)
```

The container starts as root only long enough to give the data folder to `PUID:PGID`,
then runs epub2zim as that user.

## Serving the ZIMs with Kiwix as well

Add a second service to `docker-compose.yml` that reads the same `output` folder:

```yaml
  kiwix:
    image: ghcr.io/kiwix/kiwix-serve:latest
    command: "*.zim"
    volumes:
      - ./data/output:/data
    ports:
      - "8090:8080"
```

Restart kiwix after building a new ZIM (`docker compose restart kiwix`), then browse
http://localhost:8090.

## Reaching other containers

From inside the epub2zim container, your computer is `host.docker.internal`
(set up in `docker-compose.yml`). From **another** container (e.g. Open WebUI),
epub2zim is `http://host.docker.internal:5100`, or `http://epub2zim:5100` if both
are in the same compose file / Docker network.

## Security

epub2zim has no login for the web UI: it is meant for your own computer or home network.
Don't expose port 5100 to the internet. If you must reach it remotely, put it behind a
reverse proxy with authentication, or use a VPN. The MCP endpoint is protected by the
MCP key.
