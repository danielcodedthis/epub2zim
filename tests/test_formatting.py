"""Turning article content into tidy HTML, and wiki-style links."""

from epub2zim.autolink import AutoLinker
from epub2zim.formatter import format_html, format_text, split_paragraphs
from epub2zim.settings import Settings


def test_html_is_cleaned_and_remapped():
    raw = ('<h1>Big</h1><h3>Small</h3><p onclick="x()" class="c">Hi <script>bad()</script>'
           '<a href="epub:OEBPS/ch2.xhtml#sec">there</a> <a href="epub:missing.xhtml">gone</a></p>'
           '<img src="epub:OEBPS/a.png" alt="A"><img src="epub:OEBPS/unknown.png">')
    out = format_html(raw, lambda h: "images/a.png" if h == "OEBPS/a.png" else None,
                      lambda f, frag: f"Chapter_2#{frag}" if f == "OEBPS/ch2.xhtml" else None)
    assert "<h2>Big</h2>" in out and "<h4>Small</h4>" in out          # headings shifted down one
    assert "onclick" not in out and "class=" not in out
    assert "<script" not in out
    assert 'href="Chapter_2#sec"' in out
    assert "gone" in out and "missing" not in out                      # unknown link: text kept
    assert 'src="images/a.png"' in out and "unknown" not in out


def test_paragraphs_are_rebuilt():
    text = " ".join(f"Sentence number {i} is here." for i in range(200))
    paras = split_paragraphs(text, 650)
    assert len(paras) > 3 and all(p.endswith(".") for p in paras)


def test_text_headings_and_lists():
    s = Settings(subheadings=["Main Points", "Prevalence"], detect_lists=True)
    html = format_text("Main Points A. First rule. B. Second rule. Prevalence This is common.", s)
    assert "<h2>Main Points</h2>" in html and "<h2>Prevalence</h2>" in html
    assert '<p class="li-a">A. First rule.</p>' in html
    # a phrase in the middle of a sentence is not a heading
    assert "<h2>" not in format_text("the prevalence Prevalence of things", Settings(subheadings=["Prevalence"]))


def test_autolink_first_mention_only():
    linker = AutoLinker({"Major Depressive Disorder": "MDD", "Persistent Depressive Disorder (Dysthymia)": "PDD", "Panic": "P"}, 8)
    out = linker.apply("<p>major depressive disorder and major depressive disorder; persistent depressive disorder</p>"
                       "<h2>Major Depressive Disorder</h2>", "Other")
    assert out.count('href="MDD"') == 1
    assert 'href="PDD"' in out                     # matched without the bracket part
    assert 'href="P"' not in out                   # shorter than the minimum length
    assert "<h2>Major Depressive Disorder</h2>" in out
    assert 'href="MDD"' not in linker.apply("<p>major depressive disorder</p>", "MDD")   # no self-links
