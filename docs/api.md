# REST API

The web UI uses this API; scripts can too. Interactive documentation is generated at
**`/api/docs`** while the app runs. Code: [`web/api.py`](../src/epub2zim/web/api.py).

The API has no authentication: it's for your own computer or network (see
[Docker → Security](docker.md#security)). Errors come back as `{"detail": "message"}`
with status 400 (bad input), 404 (unknown project) or 413 (file too big).

| Method | Path | Body / query | Returns |
|---|---|---|---|
| GET | `/api/health` | | `{"ok": true, "version"}` |
| GET | `/api/config` | | port, folders, MCP URL, key hint (not the key) |
| GET | `/api/config/mcp-key` | | `{"key"}` |
| GET | `/api/projects` | | list of project summaries |
| POST | `/api/projects` | multipart `file=@book.epub` | new project summary |
| GET | `/api/projects/{id}` | | summary, settings, titles, aliases, inspect report, built zims |
| DELETE | `/api/projects/{id}` | | `{"deleted": id}` |
| PUT | `/api/projects/{id}/settings` | JSON with any settings | all settings |
| PUT | `/api/projects/{id}/titles` | `{"text": "..."}` | `{"articles": n}` |
| PUT | `/api/projects/{id}/aliases` | `{"text": "..."}` | `{"aliases": n}` |
| GET | `/api/projects/{id}/pages` | `?start=1&count=3&chars=600` | page texts |
| GET | `/api/projects/{id}/find` | `?q=text&regex=false&limit=30` | matches with snippets |
| POST | `/api/projects/{id}/suggest` | `{"method","level","pattern"}` | `{"text": title list}` |
| POST | `/api/projects/{id}/preview` | | articles, misses, warnings |
| POST | `/api/projects/{id}/build` | | build report (file name, size, counts) |
| GET | `/api/projects/{id}/download/{file}` | | the .zim file |

The MCP server lives at `/mcp` (see [MCP server](mcp-server.md)).

## Example: convert from a script

```bash
BASE=http://localhost:5100/api
ID=$(curl -s -F file=@book.epub $BASE/projects | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
curl -s -X PUT $BASE/projects/$ID/settings -H 'Content-Type: application/json' \
     -d '{"language":"eng","description":"My book"}'
curl -s -X POST $BASE/projects/$ID/preview | head -c 400
FILE=$(curl -s -X POST $BASE/projects/$ID/build | python -c "import sys,json;print(json.load(sys.stdin)['file_name'])")
curl -s -o "$FILE" $BASE/projects/$ID/download/$FILE
```

## Settings keys

`title`, `description` (≤ 80), `language`, `creator`, `publisher`, `name`,
`strategy` (`toc|headings|files|titles`), `heading_level` (1–6), `clean_text`,
`page_offset` (`"auto"`, a number or `""`), `subheadings` (list), `detect_lists`,
`paragraph_size` (≥ 200), `autolink`, `autolink_min_length`, `include_images`.
See [`settings.py`](../src/epub2zim/settings.py).
