# Titles, leaving out, covers, aliases and extras

Set in step 3 of the web UI, with `update_settings` / `set_aliases` / `set_cover` over MCP,
or with CLI flags. The title tools work for every splitting strategy and run after the book
is split, in this order: renames → part names in front → leave out
(code: [`article_edits.py`](../src/epub2zim/article_edits.py)).

## Part names in front of short titles (`parent_prefix`)

Many novels number their chapters inside each part: “I”, “II”, “III”… That gives you ten
articles called “I” that nobody can search for. epub2zim puts the parent's title in front:

| Setting | Result |
|---|---|
| `short` (default) | Only titles that say nothing on their own get the prefix: Roman numerals, numbers, “Chapter 4”, “Глава 7”, “§ 3”. “Част първа · I”, but “Boats” stays “Boats” |
| `always` | Every sub-article: “The Harbour Master · Boats” |
| `never` | Titles stay as they are |

The separator is ` · ` (`prefix_separator`). When a part and its first chapter start at the
same place in the book, both are kept: the part becomes a short page listing its chapters.

## Renaming articles (`renames`)

One per line, `Old title = New title`. Matching ignores upper/lower case. Renames run before
the part prefix, so you can rename a part (`Част първа = Part One`) and its chapters follow
(“Part One · I”). To rename a chapter *with* its prefix, use the full title as shown in the
preview: `Част първа · I = Част първа · I. Горещ юли`.

## Leaving articles out (`exclude`)

One title per line. Upper/lower case doesn't matter and `*` matches anything
(`Credits*`, `*copyright*`). Both the original title and the final title are checked. The
article and its text are left out; its sub-articles stay. In the web UI's preview every row
has a ✕ button that adds the title to this list.

Typical candidates: title page, credits, “About this edition”, the printed contents page,
advertisements.

## Cover

The cover is used as the 48×48 **library icon** and at the top of the ZIM's **home page**
(`cover_on_home`, on by default).

- By default the book's own cover is used (if the EPUB marks one).
- **Upload your own** in step 3 (PNG, JPG, WebP or GIF; a square picture around 500×500 works
  best; larger pictures are shrunk to fit 1000 px). Over MCP: put the picture in `inbox/`
  and call `set_cover(project_id, file_name)`. CLI: `--cover picture.jpg`.
- Without any cover the icon is a gradient tile with the title's initials.

## Aliases (extra search names)

One per line, `Short name = Article title`:

```
PTSD = Posttraumatic Stress Disorder
Dysthymia = Persistent Depressive Disorder (Dysthymia)
The Whale = Moby-Dick
```

Each alias becomes a **redirect** in the ZIM: typing it in the reader's search box opens
the article. The article title must match exactly (case doesn't matter). Unknown titles
are skipped and reported after the build. Lines starting with `#` are comments.

## Wiki-style links (`autolink`, on by default)

The first mention of another article's title in each article becomes a link. Matching
ignores case and also tries the title without a bracket part (“Persistent Depressive
Disorder (Dysthymia)” also matches “persistent depressive disorder”). Headings and existing
links are left alone, and articles never link to themselves.

`autolink_min_length` (default 8) skips short titles, which would otherwise link common
words. Raise it if you see silly links; switch autolink off for fiction.

## Pictures (`include_images`, on by default)

Pictures used in the articles are copied into the ZIM under `images/`. Switch off for a
smaller file.

## Metadata

| Setting | Shown as | Notes |
|---|---|---|
| `title` | Library title | Readers may shorten titles over 30 characters |
| `description` | One-line description | **Max 80 characters** (a ZIM rule). If empty, the book's own description or a generic text is used, and the preview reminds you |
| `language` | Language | 3 letters (`eng`, `deu`, `fra`, `bul` …). Also picks the search index's language rules |
| `creator` | Author | From the EPUB if empty |
| `publisher` | Publisher | Defaults to `epub2zim` |
| `name` | Machine name | Made from the title + language if empty, e.g. `moby_dick_en` |

Tags `_category:other;ebook;_pictures:yes|no;_videos:no` and the date are added
automatically.
