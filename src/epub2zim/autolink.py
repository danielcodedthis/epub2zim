"""Wiki-style links: when an article mentions another article's title, link it.

Only the first mention of each title in an article is linked, matching is
case-insensitive, and text that is already a link or a heading is left alone.
A title like "Persistent Depressive Disorder (Dysthymia)" is also matched
without its bracket part ("persistent depressive disorder").
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString


class AutoLinker:
    def __init__(self, titles_to_paths: dict[str, str], min_length: int = 8):
        names: dict[str, str] = {}
        for title, path in titles_to_paths.items():
            short = re.sub(r"\s*\(.*?\)\s*", " ", title).strip()
            for variant in (title, short):
                if len(variant) >= min_length:
                    names.setdefault(variant.lower(), path)
        self.names = names
        alternatives = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
        self.rx = re.compile(rf"\b({alternatives})\b", re.I) if alternatives else None

    def apply(self, html: str, own_path: str) -> str:
        if not self.rx:
            return html
        soup = BeautifulSoup(f"<div id='__root'>{html}</div>", "lxml")
        root = soup.find(id="__root")
        linked: set[str] = {own_path}
        for text_node in list(root.find_all(string=True)):
            if not isinstance(text_node, NavigableString) or not text_node.strip():
                continue
            if text_node.find_parent(["a", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "code"]):
                continue
            original = str(text_node)
            pieces, last = [], 0
            for m in self.rx.finditer(original):
                path = self.names.get(m.group(1).lower())
                if not path or path in linked:
                    continue
                linked.add(path)
                pieces.append(original[last:m.start()])
                a = soup.new_tag("a", href=path)
                a.string = m.group(0)
                pieces.append(a)
                last = m.end()
            if pieces:
                pieces.append(original[last:])
                for piece in pieces:
                    text_node.insert_before(piece if not isinstance(piece, str) else NavigableString(piece))
                text_node.extract()
        return root.decode_contents()
