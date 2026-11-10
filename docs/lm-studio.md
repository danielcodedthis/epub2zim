# Using epub2zim from LM Studio

LM Studio (version 0.3.17 or newer) can use MCP servers with any local model that supports
tool calling. Two ways to connect: over **HTTP** (works with Docker) or over **stdio**
(LM Studio starts epub2zim itself).

## A. HTTP (recommended, works with Docker)

1. Start epub2zim (`docker compose up -d` or `epub2zim serve`).
2. Open **http://localhost:5100/#/settings** and copy the **key** (*Show* → *Copy*).
3. In LM Studio open the **Program** tab in the right sidebar (the `>_` icon) →
   **Install** → **Edit mcp.json**.
4. Add epub2zim inside `"mcpServers"` (keep any servers you already have):

   ```json
   {
     "mcpServers": {
       "epub2zim": {
         "url": "http://localhost:5100/mcp",
         "headers": {
           "Authorization": "Bearer PASTE-YOUR-KEY-HERE"
         }
       }
     }
   }
   ```

5. Save. LM Studio loads the server; **epub2zim** appears in the Program tab with its tools.

The Settings page of epub2zim shows this snippet with your address filled in.

**epub2zim on another computer?** Use that computer's address
(`http://192.168.1.20:5100/mcp`) and make sure epub2zim listens on the network (Docker does;
with pip use `epub2zim serve --host 0.0.0.0`).

## B. stdio (pip install, same computer)

If epub2zim is installed with pip on the computer running LM Studio, LM Studio can start it
on demand. No server to keep running and no key needed:

```json
{
  "mcpServers": {
    "epub2zim": {
      "command": "epub2zim",
      "args": ["mcp-stdio", "--data-dir", "/home/you/epub2zim-data"]
    }
  }
}
```

Use the full path to the `epub2zim` program if LM Studio can't find it
(`which epub2zim` on Linux/macOS, `where epub2zim` on Windows, e.g. inside your `.venv`).
Point `--data-dir` at the same folder as the web UI if you use both.

## Using it

1. Load a model with tool support (look for the hammer icon in LM Studio's model list).
2. Optional but recommended: paste the contents of
   [`skills/epub2zim-convert-book/SKILL.md`](../skills/epub2zim-convert-book/SKILL.md)
   into the chat's **System Prompt**.
3. Copy an EPUB into the data folder's `inbox/`.
4. Ask, for example:

   > Convert the book "moby-dick.epub" from the epub2zim inbox into a ZIM file.
   > Use the language eng and the description "Herman Melville's novel".

LM Studio asks for confirmation before each tool call unless you allow the tool
permanently. The model will import, inspect, preview and build, then tell you the file
name. The ZIM is in `data/output/`.

## Tips

- **Context length:** scanned books need several rounds. Give the model at least 16k tokens
  of context; 32k is comfortable.
- **The model stops after one tool call:** ask it to continue, or use a model that's better
  at tool use.
- **401 errors:** the key in `mcp.json` doesn't match. Copy it again from the Settings page.
- **Connection refused:** epub2zim isn't running, or the port/address is wrong. Open the
  same URL without `/mcp` in a browser; you should see the web UI.
