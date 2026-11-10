"""The title list and alias formats."""

import pytest

from epub2zim.titlelist import TitleListError, format_entries, parse, parse_aliases

SAMPLE = """# a comment
= Part One
Chapter One | 3
- Section A | p.12 | Section A Begins
-- Deep | 14
Chapter Two
"""


def test_parse():
    e = parse(SAMPLE)
    assert [(x.level, x.title) for x in e] == [(0, "Part One"), (1, "Chapter One"), (2, "Section A"), (3, "Deep"), (1, "Chapter Two")]
    assert e[1].page == 3 and not e[1].printed
    assert e[2].page == 12 and e[2].printed and e[2].search_text == "Section A Begins"
    assert e[4].page is None and e[4].search_text == "Chapter Two"


def test_round_trip():
    key = lambda entries: [(e.level, e.title, e.page, e.printed, e.find) for e in entries]
    assert key(parse(format_entries(parse(SAMPLE)))) == key(parse(SAMPLE))


def test_pipe_inside_search_text():
    assert parse("Bipolar I | 5 | Bipolar | Disorder")[0].find == "Bipolar | Disorder"


def test_bad_page_is_reported_with_line_number():
    with pytest.raises(TitleListError, match="Line 2"):
        parse("Fine\nBroken | twelve")


def test_aliases():
    assert parse_aliases("# c\nPTSD = Posttraumatic Stress Disorder\n\nA = B = C") == {
        "PTSD": "Posttraumatic Stress Disorder", "A": "B = C"}
    with pytest.raises(TitleListError):
        parse_aliases("no equals sign")
