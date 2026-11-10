"""The REST API, the MCP endpoint (with its key) and the command line."""

import json
import shutil

from epub2zim.config import Config

MCP_HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


def upload(client, path):
    r = client.post("/api/projects", files={"file": (path.name, path.read_bytes())})
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ------------------------------------------------------------------ web API
def test_ui_and_health(client):
    assert client.get("/api/health").json()["ok"] is True
    page = client.get("/")
    assert page.status_code == 200 and "epub" in page.text


def test_full_web_flow(client, book, config):
    pid = upload(client, book)
    data = client.get(f"/api/projects/{pid}").json()
    assert data["settings"]["title"] == "The Harbour Book"
    assert data["inspect"]["suggested_strategy"] == "toc"

    r = client.put(f"/api/projects/{pid}/settings", json={"description": "x" * 81})
    assert r.status_code == 400 and "80" in r.json()["detail"]
    assert client.put(f"/api/projects/{pid}/settings", json={"strategy": "headings", "heading_level": 2}).status_code == 200
    assert client.put(f"/api/projects/{pid}/aliases", json={"text": "Lamp = The Lighthouse"}).json() == {"aliases": 1}

    pv = client.post(f"/api/projects/{pid}/preview").json()
    assert pv["article_count"] == 5

    report = client.post(f"/api/projects/{pid}/build").json()
    assert report["articles"] == 5 and "file" not in report
    assert (config.output_dir / report["file_name"]).exists()            # copied to the library folder
    dl = client.get(f"/api/projects/{pid}/download/{report['file_name']}")
    assert dl.status_code == 200 and len(dl.content) == report["size_bytes"]

    assert client.delete(f"/api/projects/{pid}").status_code == 200
    assert client.get(f"/api/projects/{pid}").status_code == 404


def test_bad_inputs_are_friendly(client, tmp_path, book):
    r = client.post("/api/projects", files={"file": ("x.epub", b"not a zip")})
    assert r.status_code == 400 and "EPUB" in r.json()["detail"]
    assert client.get("/api/projects/..%2Fetc").status_code in (400, 404)
    pid = upload(client, book)
    r = client.put(f"/api/projects/{pid}/titles", json={"text": "A | not-a-page"})
    assert r.status_code == 400 and "Line 1" in r.json()["detail"]


def test_config_endpoint_hides_key(client):
    c = client.get("/api/config").json()
    assert c["port"] == 5100 and c["mcp_url"].endswith("/mcp")
    assert "test-key-123" not in json.dumps(c)
    assert client.get("/api/config/mcp-key").json()["key"] == "test-key-123"


# ------------------------------------------------------------------ MCP
def _rpc(client, method, params=None, id_=1, session=None, key="test-key-123"):
    headers = {**MCP_HEADERS, "Authorization": f"Bearer {key}"}
    if session:
        headers["mcp-session-id"] = session
    body = {"jsonrpc": "2.0", "method": method, **({"id": id_} if id_ else {}), **({"params": params} if params else {})}
    return client.post("/mcp", json=body, headers=headers)


def _data(response):
    """Read the JSON-RPC answer from a server-sent-events response."""
    for line in response.text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:])
    return response.json()


def _session(client):
    r = _rpc(client, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                     "clientInfo": {"name": "test", "version": "1"}})
    assert r.status_code == 200
    sid = r.headers.get("mcp-session-id")
    _rpc(client, "notifications/initialized", id_=None, session=sid)
    return sid


def test_mcp_requires_key(client):
    assert client.post("/mcp", json={}, headers=MCP_HEADERS).status_code == 401
    assert _rpc(client, "initialize", {}, key="wrong").status_code == 401


def test_mcp_tools_end_to_end(client, config, book):
    shutil.copy(book, config.inbox_dir / "harbour.epub")
    sid = _session(client)
    tools = {t["name"] for t in _data(_rpc(client, "tools/list", id_=2, session=sid))["result"]["tools"]}
    assert {"import_epub", "inspect_book", "preview_split", "build_zim", "set_title_list"} <= tools

    def call(name, **args):
        res = _data(_rpc(client, "tools/call", {"name": name, "arguments": args}, id_=3, session=sid))["result"]
        return res["content"][0]["text"], res.get("isError")

    text, _ = call("list_inbox")
    assert "harbour.epub" in text
    text, _ = call("import_epub", file_name="harbour.epub")
    pid = text.split("project_id: ")[1].split()[0]
    text, _ = call("preview_split", project_id=pid)
    assert "articles=5" in text and "Boats" in text
    text, _ = call("update_settings", project_id=pid, changes={"strategy": "nonsense"})
    assert "Not saved" in text
    text, _ = call("build_zim", project_id=pid)
    assert json.loads(text)["articles"] == 5
    # the inbox only accepts plain file names
    text, is_error = call("import_epub", file_name="../mcp_key.txt")
    assert is_error and "file name" in text


def test_mcp_auth_can_be_switched_off(tmp_path):
    from fastapi.testclient import TestClient
    from epub2zim.web import create_app
    cfg = Config(data_dir=tmp_path / "d", mcp_auth=False).prepare()
    with TestClient(create_app(cfg)) as c:
        r = c.post("/mcp", headers=MCP_HEADERS, json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}})
        assert r.status_code == 200


def test_generated_key_is_kept(tmp_path):
    a = Config(data_dir=tmp_path / "d").prepare()
    b = Config(data_dir=tmp_path / "d").prepare()
    assert a.mcp_key == b.mcp_key and a.mcp_key_source == "generated" and b.mcp_key_source == "file"


# ------------------------------------------------------------------ CLI
def test_cli_convert(book, tmp_path, capsys):
    from epub2zim.cli import main
    out = tmp_path / "cli.zim"
    main(["convert", str(book), "-o", str(out), "--strategy", "headings", "--heading-level", "1"])
    assert out.exists()
    assert '"articles": 3' in capsys.readouterr().out


def test_cli_preview_and_suggest(scanned, capsys):
    from epub2zim.cli import main
    main(["suggest", str(scanned), "--method", "running_headers"])
    assert "Soil Care" in capsys.readouterr().out
    main(["preview", str(scanned), "--strategy", "files"])
    assert "articles" in capsys.readouterr().out
