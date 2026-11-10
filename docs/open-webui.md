# Using epub2zim from Open WebUI

Open WebUI (v0.6.31 or newer) connects to MCP servers over **Streamable HTTP**, which is
exactly what epub2zim offers at `/mcp`. Only admins can add MCP servers.

## 1. Find the right address

Open WebUI usually runs in Docker, and inside a container `localhost` means *that container*,
not your computer. Pick the address that matches your setup:

| Setup | Server URL |
|---|---|
| Open WebUI **not** in Docker, epub2zim on the same computer | `http://localhost:5100/mcp` |
| Open WebUI in Docker, epub2zim on the same computer (Docker or pip) | `http://host.docker.internal:5100/mcp` |
| Both in the **same** docker compose file / Docker network | `http://epub2zim:5100/mcp` |
| epub2zim on another computer | `http://<its IP>:5100/mcp` |

On Linux, `host.docker.internal` only works if the Open WebUI container has
`extra_hosts: ["host.docker.internal:host-gateway"]` (or `--add-host` with `docker run`).
If epub2zim runs with pip, start it with `--host 0.0.0.0` so containers can reach it.

## 2. Add the server

1. Copy your key from epub2zim's **Settings** page (*Show* → *Copy*).
2. In Open WebUI: **Admin Settings → External Tools** (in some versions *Settings →
   Integrations / Tools*) → **+ Add Server / Add Connection**.
3. Fill in:
   - **Type:** `MCP (Streamable HTTP)`. Not *OpenAPI*.
   - **URL:** from the table above.
   - **Auth:** `Bearer`, **Key:** your epub2zim key.
   - **ID / Name:** `epub2zim`.
4. Save, and use the verify/refresh button: it should list epub2zim's tools.
   Restart Open WebUI if it asks.

## 3. Use it in a chat

1. Choose a model that supports **native tool calling**. In the model's settings
   (*Workspace → Models → edit → Advanced Params*) set **Function Calling** to *Native*
   if available.
2. In the chat, click **+ → Tools** (or the tools icon) and switch **epub2zim** on.
3. Optional but recommended: put the contents of
   [`skills/epub2zim-convert-book/SKILL.md`](../skills/epub2zim-convert-book/SKILL.md)
   in the model's system prompt (*Workspace → Models → System Prompt*).
4. Copy an EPUB into epub2zim's `data/inbox/` and ask:

   > Use epub2zim to convert "alice.epub" from the inbox into a ZIM file.

## Same compose file example

```yaml
services:
  epub2zim:
    build: ./epub2zim
    environment:
      EPUB2ZIM_MCP_KEY: change-me-to-a-long-random-string
    volumes: ["./epub2zim-data:/data"]
    ports: ["5100:5100"]

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports: ["3000:8080"]
    volumes: ["open-webui:/app/backend/data"]

volumes:
  open-webui:
```

Then the MCP URL in Open WebUI is `http://epub2zim:5100/mcp`.

## Older Open WebUI (before native MCP)

Use [mcpo](https://github.com/open-webui/mcpo) to turn epub2zim into an OpenAPI tool
server:

```bash
uvx mcpo --port 8000 --api-key "mcpo-key" --server-type "streamable-http" \
  --header '{"Authorization": "Bearer YOUR-EPUB2ZIM-KEY"}' -- http://localhost:5100/mcp
```

and add `http://localhost:8000` in Open WebUI as an **OpenAPI** tool server. Check
`mcpo --help` for the exact header option of your version.

## Troubleshooting

- **Verify fails / no tools:** wrong address (see step 1) or Type is not
  *MCP (Streamable HTTP)*. From inside the Open WebUI container,
  `curl http://host.docker.internal:5100/api/health` should answer `{"ok":true…}`.
- **401:** wrong key, or Auth not set to *Bearer*.
- **The model talks about the tools but never calls them:** use native function calling and
  a model trained for tool use.
