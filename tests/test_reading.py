"""Reading EPUBs and breaking them into blocks."""

import pytest

from epub2zim.blocks import book_blocks
from epub2zim.epub_reader import read_epub


@pytest.mark.parametrize("fixture", ["book", "book_ncx"])
def test_reads_metadata_and_toc(fixture, request):
    b = read_epub(request.getfixturevalue(fixture))
    assert b.title == "The Harbour Book"
    assert b.author == "Test Author"
    assert b.language == "en"
    assert len(b.docs) == 3
    assert [(t.level, t.title, t.fragment) for t in b.toc] == [
        (1, "The Lighthouse", ""), (1, "The Harbour Master", ""), (2, "Boats", "boats"),
        (2, "Nets", "nets"), (1, "Homecoming", "")]
    assert b.cover_href == "OEBPS/images/cover.png"
    assert "OEBPS/images/boat.png" in b.images


def test_book_without_toc(book_no_toc):
    assert read_epub(book_no_toc).toc == []


def test_not_an_epub(tmp_path):
    bad = tmp_path / "bad.epub"
    bad.write_text("hello")
    with pytest.raises(ValueError, match="not an EPUB"):
        read_epub(bad)


def test_blocks_keep_order_ids_and_links(book):
    blocks = book_blocks(read_epub(book))
    tags = [b.tag for b in blocks]
    assert tags[:3] == ["h1", "p", "p"]
    boats = next(b for b in blocks if b.text == "Boats")
    assert boats.heading_level == 2 and "boats" in boats.ids
    # paragraphs inside a <div> are still separate blocks
    assert any(b.tag == "ul" for b in blocks)
    # links and images are rewritten to full paths inside the zip
    link_block = next(b for b in blocks if "the end" in b.text)
    assert 'href="epub:OEBPS/ch3.xhtml#end"' in link_block.html
    fig = next(b for b in blocks if b.tag == "figure")
    assert 'src="epub:OEBPS/images/boat.png"' in fig.html
