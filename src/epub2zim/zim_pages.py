"""The pages inside the ZIM file: one style sheet, the home page and article pages.

Reader pages use a calm, Wikipedia-like layout that is easy to read for a long
time, with a dark version that follows the reader's system setting. Change the
look here; nothing else depends on it.
"""

from __future__ import annotations

import html

CSS = """
:root{--text:#202122;--soft:#54595d;--bg:#fff;--line:#c8ccd1;--box:#f8f9fa;--link:#3366cc;--accent:#e8799f}
@media (prefers-color-scheme:dark){:root{--text:#e8e6e3;--soft:#a2a9b1;--bg:#121417;--line:#3a3f45;--box:#1b1f24;--link:#88a9ff;--accent:#ff8ab6}}
*{box-sizing:border-box}
body{margin:0 auto;max-width:54rem;padding:1rem 1.25rem 3rem;font:17px/1.65 Georgia,"Times New Roman",serif;color:var(--text);background:var(--bg)}
a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
h1{font-weight:normal;font-size:2rem;line-height:1.25;border-bottom:1px solid var(--line);margin:.5rem 0 .3rem;padding-bottom:.25rem}
h2{font-weight:normal;font-size:1.45rem;border-bottom:1px solid var(--line);margin:1.7rem 0 .5rem}
h3{font-size:1.15rem;margin:1.3rem 0 .4rem}h4,h5,h6{font-size:1rem;margin:1.1rem 0 .3rem}
img{max-width:100%;height:auto}figure{margin:1rem 0;text-align:center}figcaption{font-size:.9rem;color:var(--soft)}
table{border-collapse:collapse;margin:1rem 0;font-size:.95rem;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:.3rem .55rem;vertical-align:top}th{background:var(--box)}
blockquote{margin:1rem 0;padding:.2rem 1rem;border-left:3px solid var(--line);color:var(--soft)}
pre{background:var(--box);padding:.7rem;overflow-x:auto}
.crumbs,.meta,.nav,.note,.home-intro{font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
.crumbs{font-size:.85rem;color:var(--soft)}.crumbs a{color:var(--soft)}
.meta{font-size:.8rem;color:var(--soft);margin-bottom:1rem}
.children{background:var(--box);border:1px solid var(--line);border-radius:4px;padding:.6rem 1.2rem;margin:.8rem 0 1.2rem;display:inline-block;min-width:min(100%,26rem)}
.children ul{margin:.2rem 0;padding-left:1.2rem}
.items{background:var(--box);border:1px solid var(--line);border-radius:4px;padding:.5rem 1rem;margin:.6rem 0}
.items p{margin:.35rem 0}.items .li-1{margin-left:1.6rem}.items .li-i{margin-left:3.2rem}.items .li-x{margin-left:.8rem}
.nav{display:flex;justify-content:space-between;gap:1rem;border-top:1px solid var(--line);margin-top:2.2rem;padding-top:.6rem;font-size:.88rem}
.note{font-size:.78rem;color:var(--soft);margin-top:1.2rem}
.home-cover{float:right;max-width:min(200px,38%);height:auto;margin:.4rem 0 1rem 1.2rem;border-radius:6px;box-shadow:0 6px 20px -8px rgba(0,0,0,.35)}
.home h2{clear:both}
.home-intro{color:var(--soft);font-size:.95rem}
.home ul{columns:2;column-gap:2rem;padding-left:1.2rem}.home li{break-inside:avoid;margin:.15rem 0}
.home li.l2{margin-left:1rem;list-style:circle}.home li.l3{margin-left:2rem;list-style:square}
@media (max-width:640px){body{padding:.7rem;font-size:16px}.home ul{columns:1}}
"""

OCR_NOTE = '<p class="note">This text comes from a scanned book, so a few characters may be wrong.</p>'


def _page(title: str, body: str, lang: str = "en") -> str:
    return (
        f'<!DOCTYPE html><html lang="{html.escape(lang)}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title>"
        f'<link rel="stylesheet" href="style.css"></head><body>{body}</body></html>'
    )


def _link(path: str, title: str) -> str:
    return f'<a href="{html.escape(path)}">{html.escape(title)}</a>'


def article_page(*, title: str, content_html: str, book_title: str, parents: list[tuple[str, str]],
                 children: list[tuple[str, str]], prev: tuple[str, str] | None,
                 next_: tuple[str, str] | None, page: int | None, from_scan: bool, lang: str = "en") -> str:
    """One article. parents/children/prev/next are (path, title) pairs."""
    crumbs = [_link("index", book_title)] + [_link(p, t) for p, t in parents]
    body = f'<div class="crumbs">{" › ".join(crumbs)}</div><h1>{html.escape(title)}</h1>'
    if page:
        body += f'<div class="meta">Starts on page file {page} of the book</div>'
    if children:
        body += '<div class="children"><b>In this section</b><ul>' + "".join(
            f"<li>{_link(p, t)}</li>" for p, t in children) + "</ul></div>"
    body += content_html
    body += '<div class="nav"><span>' + (f"← {_link(*prev)}" if prev else "") + "</span><span>"
    body += (f"{_link(*next_)} →" if next_ else "") + "</span></div>"
    if from_scan:
        body += OCR_NOTE
    return _page(title, body, lang)


def home_page(*, book_title: str, author: str, description: str,
              items: list[tuple[str | None, int, str, str]], lang: str = "en",
              cover_path: str | None = None) -> str:
    """The main page: cover (optional), intro, every article grouped.

    items = (group, level, path, title). cover_path = address of the cover image in the ZIM.
    No decorative symbols here: ZIM readers may not have the fonts to show them.
    """
    body = '<div class="home">'
    if cover_path:
        body += f'<img class="home-cover" src="{html.escape(cover_path)}" alt="Cover">'
    body += f"<h1>{html.escape(book_title)}</h1>"
    intro =" · ".join(x for x in (author, description) if x)
    body += f'<p class="home-intro">{html.escape(intro)}{" — " if intro else ""}Use the search box to find any word in the book.</p>'
    current_group = object()
    open_list = False
    for group, level, path, title in items:
        if group != current_group:
            if open_list:
                body += "</ul>"
            if group:
                body += f"<h2>{html.escape(group)}</h2>"
            body += "<ul>"
            open_list = True
            current_group = group
        body += f'<li class="l{min(level, 3)}">{_link(path, title)}</li>'
    if open_list:
        body += "</ul>"
    body += "</div>"
    return _page(book_title, body, lang)
