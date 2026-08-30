import json
import sys
import types
import urllib.error
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def script():
    script_path = Path(__file__).resolve().parents[1] / "goodlinks-find-dupes"
    module = types.ModuleType("goodlinks_find_dupes")
    exec(compile(script_path.read_text(), script_path, "exec"), module.__dict__)  # noqa: S102
    return module


def test_normalize_trailing_slash_removes_only_path_terminal_slash(script):
    assert (
        script.normalize_trailing_slash_url(
            "https://example.com/article/?page=2#section"
        )
        == "https://example.com/article?page=2#section"
    )


def test_normalize_trailing_slash_preserves_root_and_empty_delimiters(script):
    assert (
        script.normalize_trailing_slash_url("https://example.com/")
        == "https://example.com/"
    )
    assert (
        script.normalize_trailing_slash_url("https://example.com/article/?")
        == "https://example.com/article?"
    )
    assert (
        script.normalize_trailing_slash_url("https://example.com/article/#")
        == "https://example.com/article#"
    )


def test_build_trailing_slash_groups_excludes_unrelated_and_exact_duplicates(script):
    entries = [
        {"id": "1", "url": "https://example.com/article"},
        {"id": "2", "url": "https://example.com/article/"},
        {"id": "3", "url": "https://example.com/article/"},
        {"id": "4", "url": "https://example.com/other/"},
    ]

    groups = script.build_trailing_slash_groups(entries)

    assert [[entry["id"] for entry in group] for group in groups] == [["1", "2", "3"]]


def test_find_redirect_relations_targets_exact_saved_url_only(script):
    entries = [
        {
            "id": "1",
            "url": "https://example.com/article/",
            "normalized_url": "https://example.com/article",
            "redirect": {
                "ok": True,
                "final_url": "https://example.com/article",
                "error": None,
            },
        },
        {
            "id": "2",
            "url": "https://example.com/article/",
            "normalized_url": "https://example.com/article",
            "redirect": {
                "ok": True,
                "final_url": "https://example.com/article/",
                "error": None,
            },
        },
        {
            "id": "3",
            "url": "https://example.com/article",
            "normalized_url": "https://example.com/article",
            "redirect": {
                "ok": True,
                "final_url": "https://example.com/article",
                "error": None,
            },
        },
    ]

    assert script.find_redirect_relations(entries) == [
        {
            "from_id": "1",
            "from_url": "https://example.com/article/",
            "to_id": "3",
            "to_url": "https://example.com/article",
            "final_url": "https://example.com/article",
        }
    ]


def test_resolve_trailing_slash_groups_checks_only_candidates(script, monkeypatch):
    entries = [
        {"id": "1", "url": "https://example.com/article"},
        {"id": "2", "url": "https://example.com/article/"},
        {"id": "3", "url": "https://example.com/other"},
    ]
    groups = script.build_trailing_slash_groups(entries)
    resolved = []

    def fake_resolve(entry, timeout):
        resolved.append(entry["id"])
        entry["redirect"] = {
            "ok": True,
            "status": 200,
            "final_url": entry["url"],
            "error": None,
        }
        return entry

    monkeypatch.setattr(script, "resolve_trailing_slash_entry", fake_resolve)

    script.resolve_trailing_slash_groups(groups, workers=1, timeout=1, verbosity=-1)

    assert resolved == ["1", "2"]


def test_resolve_trailing_slash_entry_records_connection_error(script, monkeypatch):
    saved_url = "https://example.com/article/"

    def raise_url_error(request, timeout):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(script.urllib.request, "urlopen", raise_url_error)

    entry = script.resolve_trailing_slash_entry(
        {"id": "1", "url": saved_url}, timeout=1
    )

    assert entry["redirect"] == {
        "ok": False,
        "status": None,
        "final_url": saved_url,
        "error": "offline",
    }


def test_trailing_slash_highlight_lookup_failure_is_reported(script, monkeypatch):
    groups = [[{"id": "1", "url": "https://example.com/article"}]]
    monkeypatch.setattr(
        script,
        "fetch_trailing_slash_highlight_info",
        lambda link_id: {"count": None, "error": "goodlinksctl exited 4"},
    )

    script.annotate_trailing_slash_highlights(groups, workers=1, verbosity=-1)

    assert groups[0][0]["highlights"] == {
        "count": None,
        "error": "goodlinksctl exited 4",
    }


def make_link(link_id, url, read_at=None):
    return {
        "id": link_id,
        "url": url,
        "title": f"Title {link_id}",
        "tags": ["research"],
        "starred": False,
        "highlighted": False,
        "readAt": read_at,
        "wordCount": 100,
        "addedAt": "2025-01-01T00:00:00Z",
    }


def test_trailing_slash_rejects_existing_redirect_modes(script, monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["goodlinks-find-dupes", "--trailing-slash", "--follow-redirects"],
    )

    with pytest.raises(SystemExit) as exc_info:
        script.main()

    assert exc_info.value.code == 2
    assert "cannot be combined" in capsys.readouterr().err


def test_trailing_slash_json_reports_directed_redirect_and_metadata(
    script, monkeypatch, capsys
):
    monkeypatch.setattr(
        script,
        "fetch_links",
        lambda verbosity: [
            make_link("1", "https://example.com/article/"),
            make_link("2", "https://example.com/article", "2025-01-01T00:00:00Z"),
            make_link("3", "https://example.com/unrelated"),
        ],
    )

    def resolve(groups, workers, timeout, verbosity):
        for group in groups:
            for entry in group:
                entry["redirect"] = {
                    "ok": True,
                    "status": 200,
                    "final_url": "https://example.com/article",
                    "error": None,
                }

    def annotate(groups, workers, verbosity):
        for group in groups:
            for entry in group:
                entry["highlights"] = {"count": 2, "error": None}

    monkeypatch.setattr(script, "resolve_trailing_slash_groups", resolve)
    monkeypatch.setattr(script, "annotate_trailing_slash_highlights", annotate)
    monkeypatch.setattr(
        sys, "argv", ["goodlinks-find-dupes", "--trailing-slash", "--json"]
    )

    assert script.main() == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "summary\tchecked=2\tgroups=1" in captured.err
    assert output["url"] == "https://example.com/article"
    assert output["redirects"] == [
        {
            "from_id": "1",
            "from_url": "https://example.com/article/",
            "to_id": "2",
            "to_url": "https://example.com/article",
            "final_url": "https://example.com/article",
        }
    ]
    assert output["entries"][0]["highlights"] == {"count": 2, "error": None}
    assert output["entries"][1]["read_at"] == "2025-01-01T00:00:00Z"


def test_trailing_slash_json_keeps_groups_without_redirects(
    script, monkeypatch, capsys
):
    monkeypatch.setattr(
        script,
        "fetch_links",
        lambda verbosity: [
            make_link("1", "https://example.com/article/"),
            make_link("2", "https://example.com/article"),
        ],
    )

    def resolve(groups, workers, timeout, verbosity):
        for group in groups:
            for entry in group:
                entry["redirect"] = {
                    "ok": True,
                    "status": 200,
                    "final_url": entry["url"],
                    "error": None,
                }

    monkeypatch.setattr(script, "resolve_trailing_slash_groups", resolve)
    monkeypatch.setattr(
        script, "annotate_trailing_slash_highlights", lambda *args: None
    )
    monkeypatch.setattr(
        sys, "argv", ["goodlinks-find-dupes", "--trailing-slash", "--json"]
    )

    assert script.main() == 0

    output = json.loads(capsys.readouterr().out)
    assert output["redirects"] == []
