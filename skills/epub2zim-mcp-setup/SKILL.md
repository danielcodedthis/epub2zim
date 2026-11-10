---
name: epub2zim-mcp-setup
description: Help a user install epub2zim (Docker or pip) and connect its MCP server to LM Studio or Open WebUI, including the key, the right URL, and fixing connection errors. Use when the user asks how to deploy epub2zim, set up MCP, or why the assistant can't reach epub2zim.
---

# Setting up epub2zim and its MCP server

Guide the user one step at a time and ask them to confirm each step worked before moving
on. Ask early: **Docker or pip?** and **LM Studio or Open WebUI?** and **is Open WebUI
running in Docker?**

## 1. Install and start epub2zim

**Docker (recommended):**
```bash
git clone https://github.com/danielcodedthis/epub2zim.git
cd epub2zim
cp .env.example .env          # optional: change port, key, data folder
docker compose up -d
```
**pip:**
```bash
git clone https://github.com/danielcodedthis/epub2zim.git && cd epub2zim
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install .
epub2zim serve                 # add --host 0.0.0.0 if containers/other devices must reach it
```
Check: http://localhost:5100 opens, and http://localhost:5100/api/health says `{"ok":true…}`.

Settings (env vars or `.env`): `EPUB2ZIM_PORT` (5100), `EPUB2ZIM_DATA_DIR` / compose
`EPUB2ZIM_DATA` (data folder), `EPUB2ZIM_MCP_KEY` (empty = generated), `EPUB2ZIM_MCP_AUTH`
(on/off). Doc: docs/configuration.md.

## 2. Get the key

Open http://localhost:5100/#/settings → AI assistants → **Show** → **Copy**. It is sent as
`Authorization: Bearer <key>`. A generated key is stored in `data/mcp_key.txt`.

## 3a. LM Studio (0.3.17+)

Program tab (`>_`) → Install → **Edit mcp.json**:
```json
{ "mcpServers": { "epub2zim": {
    "url": "http://localhost:5100/mcp",
    "headers": { "Authorization": "Bearer <KEY>" } } } }
```
Without Docker, the stdio way also works (no key):
```json
{ "mcpServers": { "epub2zim": { "command": "epub2zim", "args": ["mcp-stdio", "--data-dir", "/path/to/data"] } } }
```
Use a model with tool support. Doc: docs/lm-studio.md.

## 3b. Open WebUI (0.6.31+)

Admin Settings → External Tools → **+** →
- Type: **MCP (Streamable HTTP)** (not OpenAPI)
- URL: pick by setup:
  - Open WebUI not in Docker: `http://localhost:5100/mcp`
  - Open WebUI in Docker, epub2zim on the same machine: `http://host.docker.internal:5100/mcp`
    (Linux: the Open WebUI container needs `extra_hosts: ["host.docker.internal:host-gateway"]`)
  - same compose file: `http://epub2zim:5100/mcp`
- Auth: **Bearer**, Key: the epub2zim key.
Then in a chat: **+ → Tools → epub2zim**, with a model using native function calling.
Doc: docs/open-webui.md.

## 4. First test

Ask the user to copy an EPUB into `data/inbox/`, then in the chat:
"Use epub2zim to list the inbox." A file list means it works. Then use the
**epub2zim-convert-book** skill.

## Fixing problems

| Symptom | Cause / fix |
|---|---|
| Connection refused / timeout | epub2zim not running, wrong port, or `localhost` used from inside a container → use `host.docker.internal` |
| 401 Unauthorized | Wrong key, or Open WebUI Auth not set to Bearer. Copy the key again |
| Open WebUI verify shows no tools | Type must be *MCP (Streamable HTTP)*; URL must end with `/mcp` |
| Model never calls tools | Model lacks tool calling, or Open WebUI not in native function-calling mode |
| “inbox is empty” | Files must be in the data folder's `inbox/` (in Docker: the mounted folder) |
| Permission denied writing data (Docker) | Set `PUID`/`PGID` in `.env` to the user's `id -u` / `id -g` |

Never ask the user to paste their key into a public place, and suggest keeping port 5100
off the internet (docs/docker.md#security).
