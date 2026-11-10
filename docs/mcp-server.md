# MCP server

epub2zim includes an [MCP](https://modelcontextprotocol.io) server, so an AI assistant can
convert books for you using the same steps as the web UI. Code:
[`mcp_server.py`](../src/epub2zim/mcp_server.py).

## Two ways to connect

| Transport | Address / command | Key needed | Use when |
|---|---|---|---|
| **Streamable HTTP** | `http://<host>:5100/mcp` | Yes | The app runs (in Docker or not) and the assistant connects over the network. LM Studio, Open WebUI, most clients |
| **stdio** | `epub2zim mcp-stdio --data-dir <folder>` | No | epub2zim is pip-installed on the same computer, and the client starts it as a program |

Both share the same data folder layout, so projects made in the web UI show up for the
assistant and the other way round (when they point at the same folder).

### The key

Send the key from the Settings page with every HTTP request:

```
Authorization: Bearer <key>
```

`X-API-Key: <key>` works too. Wrong or missing key → `401`. See
[Configuration → The MCP key](configuration.md#the-mcp-key).

### Getting books to the assistant

An assistant can't upload files. Two ways to give it a book:

1. Copy the EPUB into the data folder's **`inbox/`**, then ask the assistant to import it
   (`list_inbox` → `import_epub`).
2. Upload it in the web UI; the assistant sees it with `list_projects`.

## Tools

Every tool answers in short plain text (or compact JSON), so small local models with small
context windows can follow along.

| Tool | Arguments | What it does |
|---|---|---|
| `how_it_works` | – | Returns the workflow below. Good first call for any model |
| `list_projects` | – | `id \| name \| strategy \| last zim` per book |
| `list_inbox` | – | EPUB files waiting in `inbox/` |
| `import_epub` | `file_name` | New project from an inbox file (plain file name only). Returns `project_id` and a first look |
| `inspect_book` | `project_id` | Files, contents entries, headings, scanned or not, **suggested strategy and why** |
| `read_pages` | `project_id, start_page=1, count=3, chars=400` | Plain text of a few page files |
| `find_text` | `project_id, query, regex=false, limit=15` | Pages where text appears, with context |
| `suggest_titles` | `project_id, method, level=2, pattern="", save=false` | Make a title list: `toc`, `headings`, `running_headers`, `pattern`. `save=true` stores it |
| `get_title_list` | `project_id, start_line=1, max_lines=150` | The title list with line numbers |
| `set_title_list` | `project_id, text` | Replace the whole list (checked before saving) |
| `replace_in_title_list` | `project_id, old, new` | Small edit (first occurrence); `new=""` deletes |
| `get_settings` | `project_id` | All settings as JSON |
| `update_settings` | `project_id, changes` | e.g. `{"strategy":"headings","heading_level":2}` |
| `get_aliases` / `set_aliases` | `project_id[, text]` | `Short name = Article title` per line |
| `preview_split` | `project_id, first=1, show=40` | Article count, **misses**, warnings, and a page of the article list |
| `build_zim` | `project_id` | Builds the file; returns name, size, counts and a download link |

Errors come back as readable tool errors (“No project called …”, “Line 3: 'x' is not a
page number”), so the model can correct itself.

## The workflow (what `how_it_works` returns)

1. `list_inbox` → `import_epub(file_name)` (or `list_projects` to continue).
2. `inspect_book`: read `suggested_strategy` and `reason`.
   - `toc` / `headings` / `files`: usually go straight to preview.
   - `titles`: the book is a scan; build a title list.
3. For `titles`: `suggest_titles` (`running_headers` or `pattern`), check with `read_pages`
   and `find_text`, fix with `set_title_list` / `replace_in_title_list`.
4. `update_settings`: title, description (≤ 80 characters), language (3 letters), creator.
5. `preview_split`: check the count, the misses, very short or very long articles. Repeat.
6. Optional `set_aliases`.
7. `build_zim`, then tell the user the file name and where it is.

## Which models work well?

Any model with reliable **tool calling**. In practice:

- **Normal EPUBs** (`toc`, `headings`) need 3–5 tool calls; most 7B+ instruct models with
  tool support manage.
- **Scanned books** need a long inspect → fix → preview loop. Models around 30B and up, or
  ones tuned for tool use / coding, do much better. Keep `show` small in `preview_split`
  if the context window is small.

Ready-made instructions for assistants are in [`skills/`](../skills/README.md). Paste the
relevant `SKILL.md` into the system prompt, or load it as a skill where your client
supports that.

## Testing the endpoint by hand

```bash
curl -s -X POST http://localhost:5100/mcp \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}'
```

You should get `200` with `"serverInfo":{"name":"epub2zim"…}`. Without the key: `401`.

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
(`npx @modelcontextprotocol/inspector`) is handy for trying tools: choose *Streamable HTTP*,
URL `http://localhost:5100/mcp`, and add the `Authorization` header.

Setup guides: [LM Studio](lm-studio.md) · [Open WebUI](open-webui.md).
