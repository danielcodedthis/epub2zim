"""The four splitting strategies, the scanned-book clean-up and title suggestions."""

from epub2zim import pipeline
from epub2zim.cleaning import detect_page_offset, raw_pages
from epub2zim.epub_reader import read_epub
from epub2zim.settings import Settings

from epub_factory import FRONT_PAGES, SCAN_SECTIONS


def titles(pv):
    return [(a["level"], a["title"]) for a in pv["articles"]]


def test_toc_strategy(book):
    pv = pipeline.preview(book, Settings(strategy="toc"))
    assert titles(pv) == [(1, "The Lighthouse"), (1, "The Harbour Master"), (2, "Boats"), (2, "Nets"), (1, "Homecoming")]
    assert pv["misses"] == []
    # sections cut exactly at their ids
    boats = next(a for a in pv["articles"] if a["title"] == "Boats")
    assert boats["start"].startswith("Boats came and went")


def test_toc_strategy_without_toc_warns(book_no_toc):
    pv = pipeline.preview(book_no_toc, Settings(strategy="toc"))
    assert pv["article_count"] == 0 and pv["warnings"]


def test_headings_strategy(book_no_toc):
    one = pipeline.preview(book_no_toc, Settings(strategy="headings", heading_level=1))
    assert [t for _, t in titles(one)] == ["The Lighthouse", "The Harbour Master", "Homecoming"]
    two = pipeline.preview(book_no_toc, Settings(strategy="headings", heading_level=2))
    assert (2, "Boats") in titles(two) and len(two["articles"]) == 5


def test_files_strategy(book):
    pv = pipeline.preview(book, Settings(strategy="files"))
    assert [t for _, t in titles(pv)] == ["The Lighthouse", "The Harbour Master", "Homecoming"]


def test_inspect_suggests_strategies(book, book_no_toc, scanned):
    assert pipeline.inspect_book(book)["suggested_strategy"] == "toc"
    assert pipeline.inspect_book(book_no_toc)["suggested_strategy"] == "headings"
    report = pipeline.inspect_book(scanned)
    assert report["looks_scanned"] and report["suggested_strategy"] == "titles"


def test_page_offset_is_detected(scanned):
    assert detect_page_offset(raw_pages(read_epub(scanned))) == FRONT_PAGES


def test_running_header_suggestions_find_sections(scanned):
    text = pipeline.suggest_titles(scanned, "running_headers")
    for title, _ in SCAN_SECTIONS:
        assert title in text


def test_titles_strategy_on_scanned_book(scanned):
    titles_text = "= Garden\nGarden Basics | 5\n- Soil Care | p.7\nWatering Plants\nPest Control | 22\nNot In Book | 3\n"
    pv = pipeline.preview(scanned, Settings(strategy="titles"), titles_text)
    names = [a["title"] for a in pv["articles"]]
    assert names == ["Garden Basics", "Soil Care", "Watering Plants", "Pest Control"]
    assert pv["misses"] == ["Not In Book"]
    assert pv["articles"][1]["level"] == 2 and pv["articles"][0]["group"] == "Garden"
    # page numbers and running headers are gone from the text
    soil = pv["articles"][1]
    assert soil["start"].startswith("Main Points")


def test_pattern_suggestions(scanned):
    text = pipeline.suggest_titles(scanned, "pattern", pattern=r"((?:[A-Z]\w+ ){1,3})Main Points")
    assert "Garden Basics | 5" in text and "Pest Control" in text


def test_find_and_sample(scanned):
    hits = pipeline.find_text(scanned, "Watering Plants Main Points")
    assert hits and hits[0]["page"] == FRONT_PAGES + 6 + 5 + 1
    pages = pipeline.sample_pages(scanned, 1, 2, 20)
    assert [p["page"] for p in pages] == [1, 2] and pages[0]["text"].endswith("…") is False
