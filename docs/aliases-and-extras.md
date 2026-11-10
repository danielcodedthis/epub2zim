# Aliases and extras

Set in step 3 of the web UI, with `update_settings` / `set_aliases` over MCP, or with CLI
flags.

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
smaller file. The cover (if the EPUB marks one) is also used for the 48×48 library icon;
without a cover you get a Blush gradient tile with the title's initials.

## Metadata

| Setting | Shown as | Notes |
|---|---|---|
| `title` | Library title | Readers may shorten titles over 30 characters |
| `description` | One-line description | **Max 80 characters** (a ZIM rule) |
| `language` | Language | 3 letters (`eng`, `deu`, `fra`, `bul` …). Also picks the search index's language rules |
| `creator` | Author | From the EPUB if empty |
| `publisher` | Publisher | Defaults to `epub2zim` |
| `name` | Machine name | Made from the title + language if empty, e.g. `moby_dick_en` |

Tags `_category:other;ebook;_pictures:yes|no;_videos:no` and the date are added
automatically.
