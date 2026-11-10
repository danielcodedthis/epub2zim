# Skills for AI assistants

Each folder holds a `SKILL.md`: step-by-step instructions an AI assistant follows to use
epub2zim well. They work with any assistant:

- **Clients with skill support** (e.g. Claude, agents that read `SKILL.md` folders): copy
  the folder into the client's skills directory.
- **LM Studio, Open WebUI and others:** paste the `SKILL.md` text (without the `---` header)
  into the system prompt of the model or chat.

| Skill | Use it when the user wants to… |
|---|---|
| [`epub2zim-convert-book`](epub2zim-convert-book/SKILL.md) | convert an EPUB with the MCP tools (normal books) |
| [`epub2zim-scanned-books`](epub2zim-scanned-books/SKILL.md) | convert a scanned / OCR book with a title list |
| [`epub2zim-explain`](epub2zim-explain/SKILL.md) | understand what epub2zim does, or get help in the web UI |
| [`epub2zim-mcp-setup`](epub2zim-mcp-setup/SKILL.md) | install epub2zim and connect it to LM Studio or Open WebUI |

The skills point to files in [`docs/`](../docs/README.md) for details. If the assistant
can read files (or browse GitHub), it can open them; otherwise the skill text is enough
for the common cases.

For small local models, start with `epub2zim-convert-book` only: it's the shortest.
