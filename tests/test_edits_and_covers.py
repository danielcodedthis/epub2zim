"""Leaving articles out, renaming, parent prefixes, matched-text handling, covers,
the description warning, deleting over MCP and non-Latin file names."""

import io
import json
import shutil

import pytest
from libzim.reader import Archive
from PIL import Image

from epub2zim import pipeline
from epub2zim.article_edits import is_short_title
from epub2zim.projects import slugify
from epub2zim.settings import Settings

from epub_factory import make_novel_epub


@pytest.fixture
def novel(tmp_path):
    return make_novel_epub(tmp_path / "novel.epub")


def titles(pv):
    return [a["title"] for a in pv["articles"]]


def png(color=(94, 143, 224), size=(500, 500)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


# ------------------------------------------------------------------ titles
def test_short_titles_get_their_part_in_front(novel):
    pv = pipeline.preview(novel, Settings(strategy="toc"))
    assert "Част първа · I" in titles(pv) and "Част втора · II" in titles(pv)
    # a part and its first chapter start in the same file: both are kept
    assert titles(pv)[1:3] == ["Част първа", "Част първа · I"]
    chapter = next(a for a in pv["articles"] if a["title"] == "Част първа · I")
    assert chapter["renamed_from"] == "I" and chapter["start"].startswith("В началото")


def test_parent_prefix_never_and_always(novel, book):
    never = pipeline.preview(novel, Settings(strategy="toc", parent_prefix="never"))
    assert titles(never).count("I") == 2
    always = pipeline.preview(book, Settings(strategy="toc", parent_prefix="always"))
    assert "The Harbour Master · Boats" in titles(always)
    short = pipeline.preview(book, Settings(strategy="toc"))
    assert "Boats" in titles(short)                       # real titles are left alone


def test_is_short_title():
    for t in ("I", "XIV", "iv", "3", "12.", "Chapter 4", "Глава 7", "Част II", "§ 3"):
        assert is_short_title(t), t
    for t in ("Boats", "Introduction", "Immortality", "Chapter One"):
        assert not is_short_title(t), t


def test_exclude_with_wildcards_and_any_case(novel):
    pv = pipeline.preview(novel, Settings(strategy="toc", exclude=["заглавна*", "ЗАСЛУГИ"]))
    assert "Заглавна страница" not in titles(pv) and "Заслуги" not in titles(pv)
    assert pv["excluded"] == ["Заглавна страница", "Заслуги"]


def test_renames(novel):
    pv = pipeline.preview(novel, Settings(strategy="toc", renames=["Част първа = Part One"]))
    assert "Part One" in titles(pv) and "Part One · I" in titles(pv)


def test_bad_rename_line_is_rejected():
    with pytest.raises(ValueError, match="Old title = New title"):
        Settings.from_dict({"renames": ["no equals sign"]})


# ------------------------------------------------------------------ titles strategy text
def test_sentence_used_as_search_text_is_kept(scanned):
    sentence = "Compost 1 is page 1 of the garden basics section."
    pv = pipeline.preview(scanned, Settings(strategy="titles"), f"Garden Basics | 5 | {sentence}")
    # it is a sentence, not a heading: it must stay in the article
    assert pv["articles"][-1]["start"].startswith("Compost 1 is page 1")


def test_heading_text_is_dropped_unless_switched_off(scanned):
    on = pipeline.preview(scanned, Settings(strategy="titles"), "Soil Care | 11")
    assert on["articles"][-1]["start"].startswith("Main Points")
    off = pipeline.preview(scanned, Settings(strategy="titles", drop_heading_text=False), "Soil Care | 11")
    assert off["articles"][-1]["start"].startswith("Soil Care Main Points")


# ------------------------------------------------------------------ description, cover, home page
def test_missing_description_is_warned(book):
    assert any("No description" in w for w in pipeline.preview(book, Settings())["warnings"])
    assert not any("No description" in w for w in pipeline.preview(book, Settings(description="Hi"))["warnings"])


def test_uploaded_cover_goes_on_home_page_and_icon(novel, tmp_path):
    out = tmp_path / "n.zim"
    pipeline.build(novel, Settings(strategy="toc", description="Роман"), out, cover_png=png())
    zim = Archive(out)
    home = bytes(zim.get_entry_by_path("index").get_item().content).decode()
    assert 'src="images/_epub2zim_cover.png"' in home
    assert "✿" not in home                                      # no symbols readers can't draw
    zim.get_entry_by_path("images/_epub2zim_cover.png")
    assert zim.get_illustration_item(48).content                # icon present


def test_book_cover_used_when_nothing_uploaded(book, tmp_path):
    out = tmp_path / "b.zim"
    pipeline.build(book, Settings(), out)
    home = bytes(Archive(out).get_entry_by_path("index").get_item().content).decode()
    assert "_epub2zim_cover" in home
    pipeline.build(book, Settings(cover_on_home=False), out)
    home = bytes(Archive(out).get_entry_by_path("index").get_item().content).decode()
    assert "_epub2zim_cover" not in home


def test_cover_api(client, book):
    pid = client.post("/api/projects", files={"file": ("b.epub", book.read_bytes())}).json()["id"]
    assert client.get(f"/api/projects/{pid}/cover").status_code == 200          # the book's own cover
    r = client.post(f"/api/projects/{pid}/cover", files={"file": ("c.jpg", png((232, 121, 159), (2000, 1500)))})
    assert r.status_code == 200
    img = Image.open(io.BytesIO(client.get(f"/api/projects/{pid}/cover").content))
    assert max(img.size) == 1000                                                # shrunk to fit
    assert client.post(f"/api/projects/{pid}/cover", files={"file": ("x.png", b"nope")}).status_code == 400
    assert client.delete(f"/api/projects/{pid}/cover").status_code == 200


# ------------------------------------------------------------------ MCP: delete and cover
def test_mcp_delete_and_cover(client, config, book):
    from test_web_and_mcp import _data, _rpc, _session
    shutil.copy(book, config.inbox_dir / "b.epub")
    (config.inbox_dir / "cover.png").write_bytes(png())
    sid = _session(client)

    def call(name, **args):
        res = _data(_rpc(client, "tools/call", {"name": name, "arguments": args}, id_=5, session=sid))["result"]
        return res["content"][0]["text"]

    pid = call("import_epub", file_name="b.epub").split("project_id: ")[1].split()[0]
    assert "Cover saved" in call("set_cover", project_id=pid, file_name="cover.png")
    report = json.loads(call("build_zim", project_id=pid))
    assert report["articles"] == 5
    assert "confirm=true" in call("delete_project", project_id=pid)              # asks first
    assert client.get(f"/api/projects/{pid}").status_code == 200
    assert "Deleted" in call("delete_project", project_id=pid, confirm=True)
    assert client.get(f"/api/projects/{pid}").status_code == 404


# ------------------------------------------------------------------ names
def test_non_latin_titles_give_readable_file_names():
    assert slugify("Престъпление и наказание") == "prestaplenie-i-nakazanie"
    assert slugify("Les Misérables") == "les-miserables"
    assert slugify("!!!") == "book"


def test_cli_exclude_and_cover(novel, tmp_path, capsys):
    from epub2zim.cli import main
    cover = tmp_path / "c.png"
    cover.write_bytes(png())
    out = tmp_path / "cli.zim"
    main(["convert", str(novel), "-o", str(out), "--exclude", "Заслуги", "--exclude", "Заглавна*",
          "--cover", str(cover), "--description", "Роман"])
    report = json.loads(capsys.readouterr().out.split("✿")[0])
    assert report["excluded"] == ["Заглавна страница", "Заслуги"]
