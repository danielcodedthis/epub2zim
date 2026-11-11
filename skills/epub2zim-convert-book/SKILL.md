---
name: epub2zim-convert-book
description: Convert an EPUB book into a searchable ZIM file using the epub2zim MCP tools. Use when the user asks to convert, turn, or make a ZIM/Kiwix/Zimi file from an EPUB or ebook.
---

# Convert an EPUB to a ZIM with epub2zim

You have the epub2zim MCP tools. They work on **projects** (one per book) in epub2zim's
data folder. Work step by step, read each tool answer, and keep the user informed in one
short sentence per step.

## Steps

1. **Find the book.**
   - Call `list_projects`. If the book is already there, use its `project_id`.
   - Otherwise call `list_inbox` and then `import_epub(file_name)` with the exact file name.
   - If the inbox is empty, tell the user: "Copy the EPUB into epub2zim's data/inbox
     folder, or upload it in the web UI (http://localhost:5100), then ask me again."

2. **Look at it.** Call `inspect_book(project_id)`. Note `suggested_strategy` and `reason`.
   - `toc`, `headings` or `files` → continue with step 3.
   - `titles` (the book looks scanned) → follow the **epub2zim-scanned-books** skill
     instead, or tell the user it needs a title list (docs/scanned-books.md).

3. **Set the details.** Call `update_settings(project_id, changes)` with what you know,
   e.g. `{"title": "...", "language": "eng", "description": "..."}`.
   - Always set a `description` (one line, **80 characters or fewer**). If you leave it
     empty, the preview shows a reminder and a generic text is used.
   - `language` is 3 letters: eng, deu, fra, spa, ita, bul, rus…
   - Only change `strategy` if step 4 shows a problem.

4. **Preview.** Call `preview_split(project_id)`. Check:
   - `articles=` is sensible for the book (not 0 or 1 for a whole novel; not thousands).
   - Any `MISSES` or `WARNING` lines.
   - `LEFT OUT` lines show articles the exclude list removed.
   - Fixes: 0 articles with `toc` → `update_settings {"strategy": "headings", "heading_level": 2}`.
     Articles too big → `headings` with `heading_level` 2 or 3. Nothing works →
     `{"strategy": "files"}`. Preview again after each change.
   - **Junk pages** (title page, credits, "About this edition", printed contents):
     `update_settings {"exclude": ["Title page", "Credits*"]}`. Use the exact titles from the
     preview; `*` matches anything; case doesn't matter. Tell the user what you left out.
   - **Chapters called only "I", "II", "3"**: the default `parent_prefix: "short"` already
     makes them "Part One · I". If titles are still unclear, use
     `{"renames": ["Old title = New title"]}` (exact titles from the preview).

5. **Aliases and cover (optional).** If the book has common abbreviations or alternative
   names, call `set_aliases` with lines like `ADHD = Attention-Deficit/Hyperactivity Disorder`.
   The right side must be an exact article title from the preview. If the user put a picture
   in the inbox for the cover, call `set_cover(project_id, file_name)`.

6. **Build.** Call `build_zim(project_id)`. Then tell the user:
   - the file name and size, and how many articles;
   - the download link from the answer, and that a copy is in epub2zim's `data/output` folder;
   - any `misses` or `alias_misses`.

## Rules

- Don't invent file names or project ids: take them from tool answers.
- Don't replace a title list the user wrote without asking.
- To clean up, `delete_project(project_id)` first explains what would be deleted. Ask the user,
  then call it again with `confirm=true`. Never delete a project you didn't create without asking.
- If a tool returns an error, read it, fix the input, and try once more. If it fails again,
  explain the error to the user.
- Keep `preview_split`'s `show` small (e.g. 30) if your context is short; use `first` to page.
- Remind the user that ZIMs of copyrighted books are for personal use only, if relevant.

More detail: docs/mcp-server.md and docs/splitting-strategies.md in the epub2zim project.
