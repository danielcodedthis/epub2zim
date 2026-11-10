# Using the web UI

Open **http://localhost:5100** (or your chosen port). There are three pages:
**Books**, **Help** and **Settings**.

## Books (start page)

- **Drop an EPUB** on the dashed box, or click it to choose a file. The book is copied into
  the data folder; nothing leaves your computer.
- **Your books** lists everything you added, with its strategy and whether a ZIM was built.
  Click a card to open it.

## One book: five steps

A book page shows five numbered cards. The buttons at the top jump to each step.
**Changes save automatically** a moment after you stop typing (“✓ All changes saved” under
the title), and always right before Preview and Build.

### 1 · Look at the book

What epub2zim found: title, author, number of files, table-of-contents entries, headings
and pictures, plus a **suggestion** with the reason.

*Peek inside* lets you read any **page file** (1 = the first HTML file in the book) and
**search** for words, or a regular expression. Use it to check where a chapter really
starts and how its title is spelled, which matters for scanned books.

### 2 · Choose how to split

Four cards, one per [strategy](splitting-strategies.md):

| Card | Use it for |
|---|---|
| 📖 Table of contents | Most EPUBs |
| 🔖 Headings | Missing or too-short contents list. Pick the level (h1 only, h1–h2, …) |
| 🗂️ One per file | Fallback that always works |
| ✍️ Title list | Scanned books, or full control |

Choosing **Title list** opens the editor:

- **Fill from:** *Table of contents*, *Headings*, *Running headers (scans)* or a
  *pattern* (regular expression with one `( )` group for the title). This replaces the list
  after asking.
- **Title list:** edit freely. The format is shown under *Title list format* and in
  [Title list format](title-list-format.md).
- **Scanned-book clean-up:** remove page numbers/headers, page offset, paragraph length,
  list detection and *section headings* (phrases like “Prevalence” that become headings
  inside articles).

### 3 · Name & extras

Title, author, language (3 letters: `eng`, `deu`, `fra`, `bul` …), a short description
(max 80 characters), and under *More file details* the publisher and short name.

**Extras:** wiki-style links between articles, pictures on/off, and **aliases**: extra
search names (`PTSD = Posttraumatic Stress Disorder`). See
[Aliases and extras](aliases-and-extras.md).

### 4 · Preview articles

Click **Preview articles**. Nothing is written. You see:

- chips with the number of articles, total size, page offset, and counts of
  **very short** (under 150 characters) and **very long** (over 80,000) articles;
- a red box listing titles that were **not found** (title list strategy);
- the full table: number, title (indented by level), page file, size and first words.

Fix steps 2–3 and preview again as often as you like.

### 5 · Build the ZIM

The gradient **Build ZIM file** button writes the file with a full-text search index.
When it's done you get the file name, size, counts, a **Download** button, and a copy in the
data folder's `output` folder. Earlier builds are listed below.

At the very bottom: **Delete this book and its ZIM files…** (asks first; copies in `output`
are kept).

## Help

A short guide inside the app, with links to these docs.

## Settings

- **Storage:** data, inbox and output folders, port, upload limit, version.
- **AI assistants (MCP):** the server address, whether the key check is on, the key
  (*Show* / *Copy*), and copy-ready setup for **LM Studio** and **Open WebUI**.
- **Theme:** *Blush* (light) or *Midnight* (dark), remembered in this browser.

## Phones and tablets

The pages work on narrow screens. If epub2zim runs on another computer, open
`http://<that computer's IP>:5100` (see [Configuration](configuration.md#listening-address)).
