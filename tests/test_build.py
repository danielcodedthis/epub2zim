"""Building real .zim files and reading them back with libzim."""

from libzim.reader import Archive
from libzim.search import Query, Searcher
from libzim.suggestion import SuggestionSearcher

from epub2zim import pipeline
from epub2zim.settings import Settings


def html_of(zim, path):
    return bytes(zim.get_entry_by_path(path).get_item().content).decode()


def test_build_normal_book(book, tmp_path):
    out = tmp_path / "harbour.zim"
    report = pipeline.build(book, Settings(strategy="toc", description="Short test"), out,
                            aliases_text="Lamp = The Lighthouse\nNope = Missing Title")
    assert out.exists() and report["articles"] == 5 and report["images"] == 1
    assert report["aliases"] == 1 and report["alias_misses"] == ["Nope = Missing Title"]

    zim = Archive(out)
    assert zim.main_entry.get_item().path == "index"
    assert zim.has_fulltext_index and zim.has_title_index
    assert bytes(zim.get_metadata("Language")).decode() == "eng"
    assert bytes(zim.get_metadata("Description")).decode() == "Short test"

    boats = html_of(zim, "Boats")
    assert "The Harbour Master" in boats                  # breadcrumb to the parent
    assert 'href="Homecoming#end"' in boats               # internal link remapped to the right article
    assert 'src="images/OEBPS_images_boat.png"' in boats
    zim.get_entry_by_path("images/OEBPS_images_boat.png")

    lighthouse = html_of(zim, "The_Lighthouse")
    assert 'href="The_Harbour_Master"' in lighthouse      # wiki-style autolink
    assert zim.get_entry_by_path("Lamp").get_redirect_entry().path == "The_Lighthouse"

    results = list(Searcher(zim).search(Query().set_query("mended")).get_results(0, 5))
    assert "Nets" in results                              # full-text search works
    suggest = SuggestionSearcher(zim).suggest("harb")
    assert "The_Harbour_Master" in list(suggest.get_results(0, 5))


def test_build_scanned_book(scanned, tmp_path):
    out = tmp_path / "garden.zim"
    s = Settings(strategy="titles", subheadings=["Main Points"], detect_lists=True)
    report = pipeline.build(scanned, s, out, "Garden Basics | 5\nSoil Care | 11\nWatering Plants | 16\nPest Control | 22")
    assert report["articles"] == 4 and not report["misses"]
    page = html_of(Archive(out), "Soil_Care")
    assert "<h2>Main Points</h2>" in page and 'class="li-a"' in page
    assert "scanned book" in page                         # the OCR note


def test_duplicate_titles_get_unique_paths(book, tmp_path):
    # Two entries with the same title must not overwrite each other.
    from epub2zim.splitters.base import Article
    arts = [Article("Notes", 1, "html", "<p>a</p>"), Article("Notes", 1, "html", "<p>b</p>")]
    pipeline._assign_paths(arts)
    assert [a.path for a in arts] == ["Notes", "Notes_2"]


def test_build_with_no_articles_explains(book_no_toc, tmp_path):
    import pytest
    with pytest.raises(ValueError, match="No articles"):
        pipeline.build(book_no_toc, Settings(strategy="toc"), tmp_path / "x.zim")
