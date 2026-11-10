# Command line

Installed with pip (`pip install .`), you get the `epub2zim` command. In Docker:
`docker exec -it epub2zim epub2zim …` (files must be inside `/data`).

```
epub2zim serve        start the web UI + MCP server
epub2zim mcp-stdio    MCP server over stdio (for AI clients that start it themselves)
epub2zim inspect      describe a book and suggest a strategy
epub2zim suggest      print a suggested title list
epub2zim preview      list the articles that would be made
epub2zim convert      make the .zim file
```

Add `--help` to any command for all options.

## serve

```bash
epub2zim serve [--port 5100] [--host 127.0.0.1] [--data-dir ./data] [--mcp-key KEY] [--no-mcp-auth]
```

## mcp-stdio

```bash
epub2zim mcp-stdio [--data-dir ./data]
```

Speaks MCP on standard input/output. Meant to be started by an MCP client
(see [LM Studio](lm-studio.md#b-stdio-pip-install-same-computer)).

## inspect

```bash
epub2zim inspect book.epub
```

Prints JSON: title, author, files, contents entries, headings, page offset,
`looks_scanned`, `suggested_strategy` and `reason`.

## suggest

```bash
epub2zim suggest book.epub --method toc|headings|running_headers|pattern [--level 2] [--pattern REGEX] > titles.txt
```

## preview and convert

Both take the same splitting options:

| Option | Meaning |
|---|---|
| `--strategy toc\|headings\|files\|titles` | How to split (default `toc`) |
| `--heading-level N` | `headings`: split at h1..hN |
| `--titles FILE` | Title list (for `--strategy titles`) |
| `--page-offset auto\|N\|""` | Scanned books |
| `--subheading TEXT` | Phrase that becomes a heading (repeat for more) |
| `--lists` | Put `A. …` / `1. …` items on their own lines |
| `--no-links` | No wiki-style links |
| `--title`, `--language`, `--description`, `--creator` | Metadata |

`convert` also has `-o/--output FILE.zim` (default: next to the EPUB) and
`--aliases FILE`.

## Examples

```bash
# A normal book
epub2zim convert alice.epub --language eng --description "Lewis Carroll's classic"

# Smaller articles
epub2zim preview manual.epub --strategy headings --heading-level 3

# A scanned book
epub2zim suggest scan.epub --method running_headers > titles.txt
#   ...edit titles.txt...
epub2zim preview scan.epub --strategy titles --titles titles.txt
epub2zim convert scan.epub --strategy titles --titles titles.txt \
    --subheading "Diagnostic Features" --subheading "Prevalence" --lists \
    --aliases aliases.txt -o scan.zim
```
