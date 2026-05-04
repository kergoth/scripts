import json
import socket
import ssl
import types
import asyncio
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import httpx
import pytest
from rich.console import Console
from rich.table import Table


@pytest.fixture(scope="module")
def script():
    """Load the uv script by extracting and executing its code."""
    script_path = Path(__file__).resolve().parents[1] / "reader-tools"
    script_text = script_path.read_text()

    # Extract the code after the shebang and the /// script block
    lines = script_text.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        if line == '# ///':
            start_idx = i + 1
            break

    code = '\n'.join(lines[start_idx:])

    # Create a module and execute the script code in it
    mod = types.ModuleType("reader_tools")
    exec(code, mod.__dict__)
    return mod


def render_table_text(table: Table) -> str:
    out = StringIO()
    Console(file=out, width=120, color_system=None).print(table)
    return out.getvalue()


def test_resolve_token_env(script, monkeypatch):
    monkeypatch.setenv("READWISE_TOKEN", "env-token-123")
    assert script.resolve_token() == "env-token-123"


def test_resolve_token_cli_config(script, monkeypatch, tmp_path):
    monkeypatch.delenv("READWISE_TOKEN", raising=False)
    (tmp_path / ".readwise-cli.json").write_text(json.dumps({"token": "cli-token-456"}))
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    assert script.resolve_token() == "cli-token-456"


def test_resolve_token_missing(script, monkeypatch):
    monkeypatch.delenv("READWISE_TOKEN", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: Path("/nonexistent-path-xyz")))
    with pytest.raises(SystemExit):
        script.resolve_token()


def test_save_and_load_doc(script, tmp_path, monkeypatch):
    monkeypatch.setattr(script, "cache_root", lambda: tmp_path)
    doc = {"id": "abc123", "url": "https://example.com", "title": "Test"}
    script.save_doc(doc)
    loaded = script.load_cache()
    assert loaded == [doc]


def test_load_cache_empty(script, tmp_path, monkeypatch):
    monkeypatch.setattr(script, "cache_root", lambda: tmp_path / "empty")
    assert script.load_cache() == []


def test_meta_roundtrip(script, tmp_path, monkeypatch):
    monkeypatch.setattr(script, "cache_root", lambda: tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    script.save_meta({"last_refresh": "2024-01-01T00:00:00+00:00", "full": True})
    assert script.load_meta()["last_refresh"] == "2024-01-01T00:00:00+00:00"


def make_doc(id, url="https://ex.com", highlights=0, tags=None, location="new",
             created="2024-01-01T00:00:00Z"):
    return {
        "id": id,
        "source_url": url,
        "num_highlights": highlights,
        "tags": {t: {} for t in (tags or [])},
        "location": location,
        "created_at": created,
    }


def test_normalize_url(script):
    assert script.normalize_url("  HTTPS://Example.COM/path  ") == "https://example.com/path"
    assert script.normalize_url("") == ""


def test_score_doc(script):
    doc = make_doc("1", highlights=3, tags=["a", "b"], location="shortlist")
    assert script.score_doc(doc) == (3, 2, 4, 1)


def test_parse_args_defaults_to_dedupe(script):
    args = script.parse_args([])
    assert args.command == "dedupe"
    assert args.max_age == 3600


def test_parse_args_explicit_dedupe(script):
    args = script.parse_args(["dedupe", "--refresh", "-n"])
    assert args.command == "dedupe"
    assert args.refresh
    assert args.dry_run


def test_parse_args_explicit_stats(script):
    args = script.parse_args(["stats", "--max-age", "42", "-v", "--all-locations", "--no-refresh"])
    assert args.command == "stats"
    assert args.max_age == 42
    assert args.verbose == 1
    assert args.all_locations
    assert args.no_refresh


def test_parse_args_explicit_check_links(script):
    args = script.parse_args([
        "check-links",
        "--no-refresh",
        "--concurrency", "25",
        "--timeout", "10",
        "--retries", "3",
        "-F", "csv",
        "-v",
    ])
    assert args.command == "check-links"
    assert args.no_refresh
    assert args.concurrency == 25
    assert args.timeout == 10
    assert args.retries == 3
    assert args.format == "csv"
    assert args.verbose == 1


def test_parse_args_explicit_tag_check_links(script):
    args = script.parse_args([
        "tag-check-links",
        "--no-refresh",
        "--batch-size", "25",
        "--tag-prefix", "link",
        "-n",
        "-v",
        "check-links.csv",
    ])
    assert args.command == "tag-check-links"
    assert args.no_refresh
    assert args.batch_size == 25
    assert args.tag_prefix == "link"
    assert args.dry_run
    assert args.verbose == 1
    assert args.csv_file == "check-links.csv"


def test_parse_args_check_links_rejects_negative_retries(script):
    with pytest.raises(SystemExit) as exc_info:
        script.parse_args(["check-links", "--retries", "-1"])
    assert exc_info.value.code == 2


def test_parse_args_check_links_rejects_non_positive_timeout(script):
    with pytest.raises(SystemExit) as exc_info:
        script.parse_args(["check-links", "--timeout", "0"])
    assert exc_info.value.code == 2


def test_parse_args_allows_global_flags_before_stats_subcommand(script):
    args = script.parse_args(["-v", "stats", "--no-refresh"])
    assert args.command == "stats"
    assert args.verbose == 1
    assert args.no_refresh


def test_parse_args_allows_global_flags_before_check_links_subcommand(script):
    args = script.parse_args(["-q", "check-links", "--no-refresh"])
    assert args.command == "check-links"
    assert args.quiet == 1
    assert args.no_refresh


def test_parse_args_allows_global_flags_before_tag_check_links_subcommand(script):
    args = script.parse_args(["-q", "tag-check-links", "--no-refresh"])
    assert args.command == "tag-check-links"
    assert args.quiet == 1
    assert args.no_refresh


def test_parse_args_top_level_help(script, capsys):
    with pytest.raises(SystemExit) as exc_info:
        script.parse_args(["-h"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "Readwise Reader library maintenance utilities" in out
    assert "dedupe" in out
    assert "stats" in out


def test_classify_status_404_dead(script):
    cls, reason, retriable = script.classify_status_code(404)
    assert (cls, reason, retriable) == ("dead", "http_404", False)


def test_classify_status_410_dead(script):
    cls, reason, retriable = script.classify_status_code(410)
    assert (cls, reason, retriable) == ("dead", "http_410", False)


def test_classify_status_503_error_retriable(script):
    cls, reason, retriable = script.classify_status_code(503)
    assert (cls, reason, retriable) == ("error", "http_503", True)


def test_classify_status_retriable_client_codes(script):
    assert script.classify_status_code(408) == ("error", "http_408", True)
    assert script.classify_status_code(425) == ("error", "http_425", True)
    assert script.classify_status_code(429) == ("error", "http_429", True)


def test_classify_status_non_404_410_client_error_dead(script):
    assert script.classify_status_code(451) == ("dead", "http_451", False)


def test_classify_status_success_and_redirect_not_reported(script):
    assert script.classify_status_code(200) == (None, None, False)
    assert script.classify_status_code(301) == (None, None, False)


def test_classify_request_exception_timeout_dead_retriable(script):
    req = httpx.Request("GET", "https://example.com")
    exc = httpx.ConnectTimeout("timed out", request=req)
    cls, reason, retriable = script.classify_request_exception(exc)
    assert (cls, reason, retriable) == ("dead", "timeout", True)


def test_classify_request_exception_dns_dead_non_retriable(script):
    req = httpx.Request("GET", "https://example.com")
    exc = httpx.ConnectError(
        "failed to lookup address information: nodename nor servname provided, or not known",
        request=req,
    )
    cls, reason, retriable = script.classify_request_exception(exc)
    assert (cls, reason, retriable) == ("dead", "dns", False)


def test_classify_request_exception_dns_via_exception_chain_type(script):
    req = httpx.Request("GET", "https://example.com")
    exc = httpx.ConnectError("connect failed", request=req)
    exc.__cause__ = socket.gaierror(-2, "Name or service not known")
    cls, reason, retriable = script.classify_request_exception(exc)
    assert (cls, reason, retriable) == ("dead", "dns", False)


def test_classify_request_exception_tls_dead_non_retriable(script):
    req = httpx.Request("GET", "https://example.com")
    exc = httpx.ConnectError(
        "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed",
        request=req,
    )
    cls, reason, retriable = script.classify_request_exception(exc)
    assert (cls, reason, retriable) == ("dead", "tls", False)


def test_classify_request_exception_tls_via_exception_chain_type(script):
    req = httpx.Request("GET", "https://example.com")
    exc = httpx.ConnectError("connect failed", request=req)
    exc.__cause__ = ssl.SSLError("CERTIFICATE_VERIFY_FAILED")
    cls, reason, retriable = script.classify_request_exception(exc)
    assert (cls, reason, retriable) == ("dead", "tls", False)


def test_classify_request_exception_connect_dead_retriable(script):
    req = httpx.Request("GET", "https://example.com")
    exc = httpx.ConnectError("connection refused", request=req)
    cls, reason, retriable = script.classify_request_exception(exc)
    assert (cls, reason, retriable) == ("dead", "connect", True)


def test_classification_retriable_semantics_timeout_and_connect(script):
    # classification/reason are the final classification if retries are exhausted.
    # retriable=True signals caller should retry first.
    req = httpx.Request("GET", "https://example.com")
    timeout_exc = httpx.ConnectTimeout("timed out", request=req)
    connect_exc = httpx.ConnectError("connection refused", request=req)
    assert script.classify_request_exception(timeout_exc) == ("dead", "timeout", True)
    assert script.classify_request_exception(connect_exc) == ("dead", "connect", True)


def test_normalize_tag_component(script):
    assert script.normalize_tag_component(" HTTP 404 ") == "http_404"
    assert script.normalize_tag_component("dns") == "dns"
    assert script.normalize_tag_component("___") == "unknown"


def test_group_check_links_rows(script):
    rows = [
        {"id": "a", "classification": "dead", "reason": "http_404"},
        {"id": "b", "classification": "dead", "reason": "http_404"},
        {"id": "c", "classification": "dead", "reason": "dns"},
    ]
    grouped = script.group_check_links_rows(rows, "link")
    assert grouped["link_dead_http_404"] == {"a", "b"}
    assert grouped["link_dead_dns"] == {"c"}


def test_get_doc_tag_names(script):
    assert script.get_doc_tag_names({"tags": {"a": {}, "b": {}}}) == {"a", "b"}
    assert script.get_doc_tag_names({"tags": ["a", "b"]}) == {"a", "b"}
    assert script.get_doc_tag_names({"tags": [{"name": "a"}, {"key": "b"}]}) == {"a", "b"}


def test_bulk_update_documents_handles_207_partial_failures(script, monkeypatch):
    class FakeResponse:
        def __init__(self):
            self.status_code = 207
            self.headers = {}

        def json(self):
            return {
                "results": [
                    {"id": "ok-1", "success": True},
                    {"id": "bad-1", "success": False, "error": "Document not found"},
                ]
            }

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def patch(self, _url, json):
            assert "updates" in json
            return FakeResponse()

    monkeypatch.setattr(script.httpx, "Client", FakeClient)
    success, failures = script.bulk_update_documents(
        "token",
        [{"id": "ok-1", "tags": ["x"]}, {"id": "bad-1", "tags": ["y"]}],
    )
    assert success == {"ok-1"}
    assert failures == {"bad-1": "Document not found"}


def test_classify_request_exception_generic_error_retriable(script):
    req = httpx.Request("GET", "https://example.com")
    exc = httpx.RequestError("request failed", request=req)
    cls, reason, retriable = script.classify_request_exception(exc)
    assert (cls, reason, retriable) == ("error", "request_error", True)


def test_check_one_source_url_404_dead_no_retry_emits_row(script, monkeypatch):
    calls = {"count": 0}

    class FakeAsyncClient:
        async def get(self, url, follow_redirects=True, timeout=10):
            calls["count"] += 1
            return types.SimpleNamespace(status_code=404)

    async def _no_sleep(_seconds):
        return None

    monkeypatch.setattr(script.asyncio, "sleep", _no_sleep)
    row = {
        "id": "doc-1",
        "url": "https://rw/doc-1",
        "source_url": "https://example.com/404",
        "tag_count": 1,
        "highlight_count": 2,
    }
    out = asyncio.run(
        script.check_one_source_url(
            FakeAsyncClient(),
            row,
            timeout=10,
            retries=3,
        )
    )
    assert calls["count"] == 1
    assert out["id"] == "doc-1"
    assert out["classification"] == "dead"
    assert out["reason"] == "http_404"


def test_check_one_source_url_timeout_then_200_not_emitted(script, monkeypatch):
    req = httpx.Request("GET", "https://example.com/transient")
    outcomes = [httpx.ConnectTimeout("timed out", request=req), 200]
    calls = {"count": 0}

    class FakeAsyncClient:
        async def get(self, url, follow_redirects=True, timeout=10):
            calls["count"] += 1
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return types.SimpleNamespace(status_code=outcome)

    async def _no_sleep(_seconds):
        return None

    monkeypatch.setattr(script.asyncio, "sleep", _no_sleep)
    row = {
        "id": "doc-2",
        "url": "https://rw/doc-2",
        "source_url": "https://example.com/transient",
        "tag_count": 0,
        "highlight_count": 0,
    }
    out = asyncio.run(
        script.check_one_source_url(
            FakeAsyncClient(),
            row,
            timeout=10,
            retries=3,
        )
    )
    assert calls["count"] == 2
    assert out is None


def test_check_links_async_repeated_503_emits_error_row(script, monkeypatch):
    calls = {"count": 0}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, follow_redirects=True, timeout=10):
            calls["count"] += 1
            return types.SimpleNamespace(status_code=503)

    async def _no_sleep(_seconds):
        return None

    monkeypatch.setattr(script.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(script.asyncio, "sleep", _no_sleep)

    candidates = [{
        "id": "doc-3",
        "url": "https://rw/doc-3",
        "source_url": "https://example.com/503",
        "tag_count": 3,
        "highlight_count": 1,
    }]
    out = asyncio.run(
        script.check_links_async(
            candidates,
            concurrency=2,
            timeout=10,
            retries=2,
        )
    )
    assert calls["count"] == 3
    assert len(out) == 1
    assert out[0]["id"] == "doc-3"
    assert out[0]["classification"] == "error"
    assert out[0]["reason"] == "http_503"
    assert out[0]["tag_count"] == 3
    assert out[0]["highlight_count"] == 1


def test_check_one_source_url_propagates_internal_classification_errors(script):
    class FakeAsyncClient:
        async def get(self, url, follow_redirects=True, timeout=10):
            return types.SimpleNamespace(status_code=503)

    def _boom(_status):
        raise RuntimeError("classification bug")

    row = {
        "id": "doc-4",
        "url": "https://rw/doc-4",
        "source_url": "https://example.com/503",
        "tag_count": 0,
        "highlight_count": 0,
    }
    original = script.classify_status_code
    try:
        script.classify_status_code = _boom
        with pytest.raises(RuntimeError, match="classification bug"):
            asyncio.run(
                script.check_one_source_url(
                    FakeAsyncClient(),
                    row,
                    timeout=10,
                    retries=0,
                )
            )
    finally:
        script.classify_status_code = original


def test_should_emit_checkpoint_count_threshold(script):
    assert script.should_emit_checkpoint(
        completed=250,
        last_completed=0,
        now=5.0,
        last_time=0.0,
    )


def test_should_emit_checkpoint_time_threshold(script):
    assert script.should_emit_checkpoint(
        completed=10,
        last_completed=0,
        now=10.1,
        last_time=0.0,
    )


def test_should_emit_checkpoint_no_emit(script):
    assert not script.should_emit_checkpoint(
        completed=10,
        last_completed=0,
        now=3.0,
        last_time=0.0,
    )


def test_check_links_async_emits_checkpoint_hook_on_cadence(script):
    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, follow_redirects=True, timeout=10):
            return types.SimpleNamespace(status_code=200)

    emitted = []

    def _checkpoint(payload):
        emitted.append(payload)

    original_client = script.httpx.AsyncClient
    try:
        script.httpx.AsyncClient = FakeAsyncClient
        candidates = [
            {"id": "a", "url": "https://rw/a", "source_url": "https://a", "tag_count": 0, "highlight_count": 0},
            {"id": "b", "url": "https://rw/b", "source_url": "https://b", "tag_count": 0, "highlight_count": 0},
            {"id": "c", "url": "https://rw/c", "source_url": "https://c", "tag_count": 0, "highlight_count": 0},
        ]
        out = asyncio.run(
            script.check_links_async(
                candidates,
                concurrency=2,
                timeout=10,
                retries=0,
                checkpoint_cb=_checkpoint,
                count_interval=2,
                time_interval=999.0,
            )
        )
    finally:
        script.httpx.AsyncClient = original_client

    assert out == []
    assert len(emitted) == 2
    assert emitted[0]["completed"] == 2
    assert emitted[0]["total"] == 3
    assert emitted[-1]["completed"] == 3
    assert emitted[-1]["total"] == 3


def test_check_links_async_checkpoint_callback_exception_does_not_abort(script):
    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, follow_redirects=True, timeout=10):
            return types.SimpleNamespace(status_code=200)

    calls = {"count": 0}

    def _checkpoint(_payload):
        calls["count"] += 1
        raise RuntimeError("checkpoint callback failure")

    original_client = script.httpx.AsyncClient
    try:
        script.httpx.AsyncClient = FakeAsyncClient
        candidates = [
            {"id": "a", "url": "https://rw/a", "source_url": "https://a", "tag_count": 0, "highlight_count": 0},
            {"id": "b", "url": "https://rw/b", "source_url": "https://b", "tag_count": 0, "highlight_count": 0},
        ]
        out = asyncio.run(
            script.check_links_async(
                candidates,
                concurrency=2,
                timeout=10,
                retries=0,
                checkpoint_cb=_checkpoint,
                count_interval=1,
                time_interval=999.0,
            )
        )
    finally:
        script.httpx.AsyncClient = original_client

    assert out == []
    assert calls["count"] >= 1


def test_check_links_async_emits_terminal_checkpoint_when_cadence_not_triggered(script):
    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, follow_redirects=True, timeout=10):
            return types.SimpleNamespace(status_code=200)

    emitted = []

    def _checkpoint(payload):
        emitted.append(payload)

    original_client = script.httpx.AsyncClient
    try:
        script.httpx.AsyncClient = FakeAsyncClient
        out = asyncio.run(
            script.check_links_async(
                [{"id": "a", "url": "https://rw/a", "source_url": "https://a", "tag_count": 0, "highlight_count": 0}],
                concurrency=1,
                timeout=10,
                retries=0,
                checkpoint_cb=_checkpoint,
                count_interval=250,
                time_interval=999.0,
            )
        )
    finally:
        script.httpx.AsyncClient = original_client

    assert out == []
    assert emitted[-1]["completed"] == 1
    assert emitted[-1]["total"] == 1


def test_check_links_async_sanitizes_invalid_intervals(script):
    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, follow_redirects=True, timeout=10):
            return types.SimpleNamespace(status_code=200)

    emitted = []

    def _checkpoint(payload):
        emitted.append(payload)

    original_client = script.httpx.AsyncClient
    try:
        script.httpx.AsyncClient = FakeAsyncClient
        out = asyncio.run(
            script.check_links_async(
                [
                    {"id": "a", "url": "https://rw/a", "source_url": "https://a", "tag_count": 0, "highlight_count": 0},
                    {"id": "b", "url": "https://rw/b", "source_url": "https://b", "tag_count": 0, "highlight_count": 0},
                    {"id": "c", "url": "https://rw/c", "source_url": "https://c", "tag_count": 0, "highlight_count": 0},
                ],
                concurrency=2,
                timeout=10,
                retries=0,
                checkpoint_cb=_checkpoint,
                count_interval=0,
                time_interval=0.0,
            )
        )
    finally:
        script.httpx.AsyncClient = original_client

    assert out == []
    assert len(emitted) <= 4
    assert emitted[-1]["completed"] == 3
    assert emitted[-1]["total"] == 3


def test_choose_output_format_honors_override(script):
    assert script.choose_output_format("csv") == "csv"
    assert script.choose_output_format("plain") == "plain"
    assert script.choose_output_format("rich") == "rich"


def test_choose_output_format_defaults_rich_on_tty(script):
    class FakeStdout:
        @staticmethod
        def isatty():
            return True

    original_stdout = script.sys.stdout
    try:
        script.sys.stdout = FakeStdout()
        assert script.choose_output_format(None) == "rich"
    finally:
        script.sys.stdout = original_stdout


def test_choose_output_format_defaults_plain_when_not_tty(script):
    class FakeStdout:
        @staticmethod
        def isatty():
            return False

    original_stdout = script.sys.stdout
    try:
        script.sys.stdout = FakeStdout()
        assert script.choose_output_format(None) == "plain"
    finally:
        script.sys.stdout = original_stdout


def test_choose_progress_output_format_defaults_rich_on_tty(script):
    class FakeStderr:
        @staticmethod
        def isatty():
            return True

    original_stderr = script.sys.stderr
    try:
        script.sys.stderr = FakeStderr()
        assert script.choose_progress_output_format() == "rich"
    finally:
        script.sys.stderr = original_stderr


def test_choose_progress_output_format_defaults_plain_when_not_tty(script):
    class FakeStderr:
        @staticmethod
        def isatty():
            return False

    original_stderr = script.sys.stderr
    try:
        script.sys.stderr = FakeStderr()
        assert script.choose_progress_output_format() == "plain"
    finally:
        script.sys.stderr = original_stderr


def test_delete_documents_plain_emits_checkpoint_lines(script, monkeypatch, capsys, tmp_path):
    deleted_ids = []
    monkeypatch.setattr(script, "docs_dir", lambda: tmp_path)

    def _delete_document(_token, doc_id):
        deleted_ids.append(doc_id)
        return True

    monkeypatch.setattr(script, "delete_document", _delete_document)
    monkeypatch.setattr(script, "choose_progress_output_format", lambda: "plain")

    docs = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    deleted = script.delete_documents(
        "token",
        docs,
        count_interval=2,
        time_interval=999.0,
    )

    captured = capsys.readouterr()
    assert deleted == 3
    assert deleted_ids == ["a", "b", "c"]
    assert "checkpoint completed=2/3 deleted=2" in captured.err
    assert "checkpoint completed=3/3 deleted=3" in captured.err


def test_apply_tag_updates_plain_emits_checkpoint_lines(script, monkeypatch, capsys):
    docs_by_id = {
        "a": {"id": "a", "tags": {}},
        "b": {"id": "b", "tags": {}},
        "c": {"id": "c", "tags": {}},
    }
    updates_by_tag = {
        "link_dead_http_404": [
            {"id": "a", "tags": ["link_dead_http_404"]},
            {"id": "b", "tags": ["link_dead_http_404"]},
            {"id": "c", "tags": ["link_dead_http_404"]},
        ]
    }

    monkeypatch.setattr(script, "choose_progress_output_format", lambda: "plain")
    monkeypatch.setattr(
        script,
        "bulk_update_documents",
        lambda _token, batch: ({item["id"] for item in batch}, {}),
    )
    monkeypatch.setattr(script, "save_doc", lambda _doc: None)

    succeeded, failed = script.apply_tag_updates(
        token="token",
        updates_by_tag=updates_by_tag,
        docs_by_id=docs_by_id,
        batch_size=2,
        count_interval=2,
        time_interval=999.0,
    )

    captured = capsys.readouterr()
    assert succeeded == 3
    assert failed == 0
    assert "checkpoint completed=2/3 succeeded=2 failed=0" in captured.err
    assert "checkpoint completed=3/3 succeeded=3 failed=0" in captured.err


def test_delete_document_rate_limit_logs_at_debug(script, monkeypatch):
    class FakeResponse:
        def __init__(self, status_code, retry_after=None):
            self.status_code = status_code
            self.headers = {}
            if retry_after is not None:
                self.headers["retry-after"] = str(retry_after)

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self._responses = [
                FakeResponse(429, retry_after=7),
                FakeResponse(204),
            ]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def delete(self, _url):
            return self._responses.pop(0)

    debug_messages = []
    info_messages = []

    monkeypatch.setattr(script.httpx, "Client", FakeClient)
    monkeypatch.setattr(script.time, "sleep", lambda _wait: None)
    monkeypatch.setattr(script.log, "debug", lambda msg, *args: debug_messages.append((msg, args)))
    monkeypatch.setattr(script.log, "info", lambda msg, *args: info_messages.append((msg, args)))

    assert script.delete_document("token", "doc-1")
    assert ("Rate limited; retrying in %ds", (7,)) in debug_messages
    assert ("Rate limited; retrying in %ds", (7,)) not in info_messages


def test_render_check_links_results_csv_header_and_column_order(script, capsys):
    rows = [{
        "id": "doc-1",
        "url": "https://rw/doc-1",
        "source_url": "https://example.com/404",
        "tag_count": 2,
        "highlight_count": 5,
        "classification": "dead",
        "reason": "http_404",
    }]
    script.render_check_links_results(rows, "csv")
    out = capsys.readouterr().out.strip().splitlines()
    assert out[0] == "id,url,source_url,tag_count,highlight_count,classification,reason"
    assert out[1] == "doc-1,https://rw/doc-1,https://example.com/404,2,5,dead,http_404"


def test_run_check_links_exits_nonzero_when_failures_found(script, monkeypatch):
    monkeypatch.setattr(script, "setup_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "resolve_token", lambda: "token")
    monkeypatch.setattr(script, "refresh_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "load_cache", lambda: [{"id": "x"}])
    monkeypatch.setattr(
        script,
        "collect_check_link_candidates",
        lambda docs: [{"id": "doc-1", "url": "u", "source_url": "s", "tag_count": 0, "highlight_count": 0}],
    )

    async def _check(*args, **kwargs):
        return [{"id": "doc-1", "url": "u", "source_url": "s", "tag_count": 0, "highlight_count": 0, "classification": "dead", "reason": "http_404"}]

    monkeypatch.setattr(script, "check_links_async", _check)
    monkeypatch.setattr(script, "render_check_links_results", lambda *args, **kwargs: None)

    args = script.parse_args(["check-links", "--no-refresh", "-F", "plain"])
    with pytest.raises(SystemExit) as exc_info:
        script.run_check_links(args)
    assert exc_info.value.code == 1


def test_run_check_links_zero_exit_when_no_failures(script, monkeypatch):
    monkeypatch.setattr(script, "setup_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "resolve_token", lambda: "token")
    monkeypatch.setattr(script, "refresh_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "load_cache", lambda: [{"id": "x"}])
    monkeypatch.setattr(
        script,
        "collect_check_link_candidates",
        lambda docs: [{"id": "doc-1", "url": "u", "source_url": "s", "tag_count": 0, "highlight_count": 0}],
    )

    async def _check(*args, **kwargs):
        return []

    monkeypatch.setattr(script, "check_links_async", _check)
    monkeypatch.setattr(script, "render_check_links_results", lambda *args, **kwargs: None)

    args = script.parse_args(["check-links", "--no-refresh", "-F", "plain"])
    script.run_check_links(args)


def test_run_check_links_no_refresh_skips_refresh(script, monkeypatch):
    monkeypatch.setattr(script, "setup_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "resolve_token", lambda: "token")
    refresh_called = {"value": False}

    def _refresh(*args, **kwargs):
        refresh_called["value"] = True

    monkeypatch.setattr(script, "refresh_cache", _refresh)
    monkeypatch.setattr(script, "load_cache", lambda: [])
    monkeypatch.setattr(script, "collect_check_link_candidates", lambda docs: [])

    async def _check(*args, **kwargs):
        return []

    monkeypatch.setattr(script, "check_links_async", _check)
    monkeypatch.setattr(script, "render_check_links_results", lambda *args, **kwargs: None)

    args = script.parse_args(["check-links", "--no-refresh", "-F", "plain"])
    script.run_check_links(args)
    assert not refresh_called["value"]


def test_run_tag_check_links_dry_run(script, monkeypatch):
    monkeypatch.setattr(script, "setup_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "resolve_token", lambda: "token")
    monkeypatch.setattr(script, "refresh_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        script,
        "read_check_links_rows",
        lambda _path: [{"id": "doc-1", "classification": "dead", "reason": "http_404"}],
    )
    monkeypatch.setattr(script, "load_cache", lambda: [{"id": "doc-1", "tags": {"existing": {}}, "location": "new"}])

    bulk_calls = []
    monkeypatch.setattr(script, "bulk_update_documents", lambda *_args, **_kwargs: bulk_calls.append(1))

    args = script.parse_args(["tag-check-links", "--no-refresh", "-n", "check-links.csv"])
    script.run_tag_check_links(args)
    assert bulk_calls == []


def test_run_tag_check_links_applies_updates(script, monkeypatch):
    monkeypatch.setattr(script, "setup_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "resolve_token", lambda: "token")
    monkeypatch.setattr(script, "refresh_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        script,
        "read_check_links_rows",
        lambda _path: [{"id": "doc-1", "classification": "dead", "reason": "http_404"}],
    )

    docs = [{"id": "doc-1", "tags": {"existing": {}}, "location": "new"}]
    monkeypatch.setattr(script, "load_cache", lambda: docs)

    bulk_payloads = []

    def _bulk_update(_token, updates):
        bulk_payloads.append(updates)
        return {"doc-1"}, {}

    monkeypatch.setattr(script, "bulk_update_documents", _bulk_update)

    saved_docs = []
    monkeypatch.setattr(script, "save_doc", lambda doc: saved_docs.append(doc.copy()))

    args = script.parse_args(["tag-check-links", "--no-refresh", "check-links.csv"])
    script.run_tag_check_links(args)

    assert len(bulk_payloads) == 1
    assert bulk_payloads[0][0]["id"] == "doc-1"
    assert "link_dead_http_404" in bulk_payloads[0][0]["tags"]
    assert len(saved_docs) == 1
    assert "link_dead_http_404" in saved_docs[0]["tags"]


def test_run_check_links_csv_keeps_logs_and_checkpoints_off_stdout(script, monkeypatch, capsys):
    monkeypatch.setattr(script, "resolve_token", lambda: "token")

    def _refresh(*args, **kwargs):
        script.log.info("refresh-log-line")

    monkeypatch.setattr(script, "refresh_cache", _refresh)
    monkeypatch.setattr(script, "load_cache", lambda: [{"id": "x"}])
    monkeypatch.setattr(
        script,
        "collect_check_link_candidates",
        lambda docs: [{"id": "doc-1", "url": "https://rw/doc-1", "source_url": "https://example.com/404", "tag_count": 2, "highlight_count": 5}],
    )

    async def _check(*args, **kwargs):
        checkpoint_cb = kwargs.get("checkpoint_cb")
        if checkpoint_cb:
            checkpoint_cb({"completed": 1, "total": 1, "failures": 1, "timestamp": 123.0})
        script.log.info("async-log-line")
        return [{
            "id": "doc-1",
            "url": "https://rw/doc-1",
            "source_url": "https://example.com/404",
            "tag_count": 2,
            "highlight_count": 5,
            "classification": "dead",
            "reason": "http_404",
        }]

    monkeypatch.setattr(script, "check_links_async", _check)

    args = script.parse_args(["check-links", "-F", "csv"])
    with pytest.raises(SystemExit) as exc_info:
        script.run_check_links(args)
    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    out_lines = [line for line in captured.out.strip().splitlines() if line]
    assert out_lines[0] == "id,url,source_url,tag_count,highlight_count,classification,reason"
    assert out_lines[1] == "doc-1,https://rw/doc-1,https://example.com/404,2,5,dead,http_404"
    assert "refresh-log-line" not in captured.out
    assert "async-log-line" not in captured.out
    assert "checkpoint completed=1/1 failures=1" not in captured.out

    assert "refresh-log-line" in captured.err
    assert "async-log-line" in captured.err
    assert "checkpoint completed=1/1 failures=1" in captured.err


def test_run_check_links_progress_uses_stderr_tty_not_result_format(script, monkeypatch):
    monkeypatch.setattr(script, "setup_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "resolve_token", lambda: "token")
    monkeypatch.setattr(script, "refresh_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "load_cache", lambda: [{"id": "x"}])
    monkeypatch.setattr(
        script,
        "collect_check_link_candidates",
        lambda docs: [{"id": "doc-1", "url": "u", "source_url": "s", "tag_count": 0, "highlight_count": 0}],
    )
    monkeypatch.setattr(script, "choose_output_format", lambda _requested: "plain")
    monkeypatch.setattr(script, "choose_progress_output_format", lambda: "rich")
    monkeypatch.setattr(script, "render_check_links_results", lambda *args, **kwargs: None)

    class FakeProgress:
        was_used = False
        updates = []

        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            type(self).was_used = True
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def add_task(self, _description, total=0):
            self.total = total
            return "task-1"

        def update(self, task_id, completed=0, description=""):
            type(self).updates.append((task_id, completed, description))

    async def _check(*args, **kwargs):
        checkpoint_cb = kwargs.get("checkpoint_cb")
        if checkpoint_cb:
            checkpoint_cb({"completed": 1, "total": 1, "failures": 0, "timestamp": 1.0})
        return []

    monkeypatch.setattr(script, "Progress", FakeProgress)
    monkeypatch.setattr(script, "check_links_async", _check)

    args = script.parse_args(["check-links", "--no-refresh", "-F", "plain"])
    script.run_check_links(args)
    assert FakeProgress.was_used
    assert FakeProgress.updates


def test_collect_check_link_candidates_filters_out_unsupported_docs(script):
    docs = [
        {"id": "a", "source_url": "https://a", "url": "https://rw/a", "location": "archive", "tags": {}, "parent_id": None},
        {"id": "b", "source_url": "https://b", "url": "https://rw/b", "location": "feed", "tags": {}, "parent_id": None},
        {"id": "c", "source_url": "https://c", "url": "https://rw/c", "location": "later", "tags": {}, "parent_id": "a"},
        {"id": "d", "source_url": "", "url": "https://rw/d", "location": "later", "tags": {}, "parent_id": None},
        {"id": "e", "source_url": "https://e", "url": "https://rw/e", "location": "later", "category": "highlight", "tags": {}, "parent_id": None},
        {"id": "f", "source_url": "https://f", "url": "https://rw/f", "location": "later", "category": "note", "tags": {}, "parent_id": None},
    ]
    out = script.collect_check_link_candidates(docs)
    assert [row["id"] for row in out] == ["a"]


def test_collect_check_link_candidates_enriches_tag_and_highlight_counts(script):
    docs = [
        {"id": "p1", "source_url": "https://x", "url": "https://rw/x", "location": "archive", "tags": {"t1": {}, "t2": {}}},
        {"id": "h1", "parent_id": "p1", "category": "highlight"},
        {"id": "h2", "parent_id": "p1", "category": "highlight"},
        {"id": "n1", "parent_id": "p1", "category": "note"},
        {"id": "u1", "parent_id": "p1"},
    ]
    row = script.collect_check_link_candidates(docs)[0]
    assert row["tag_count"] == 2
    assert row["highlight_count"] == 4


def test_collect_check_link_candidates_filters_non_http_source_urls(script):
    docs = [
        {"id": "a", "source_url": "https://example.com", "url": "https://rw/a", "location": "archive", "tags": {}},
        {"id": "b", "source_url": "/reader-forwarded-email/abc123", "url": "https://rw/b", "location": "archive", "tags": {}},
        {"id": "c", "source_url": "mailto:user@example.com", "url": "https://rw/c", "location": "archive", "tags": {}},
        {"id": "d", "source_url": "http://example.com/page", "url": "https://rw/d", "location": "archive", "tags": {}},
    ]
    out = script.collect_check_link_candidates(docs)
    ids = [row["id"] for row in out]
    assert "a" in ids
    assert "d" in ids  # http:// normalized to https://, kept
    assert "b" not in ids
    assert "c" not in ids


def test_retry_backoff_seconds_schedule(script):
    assert script._retry_backoff_seconds(0) == pytest.approx(0.5)
    assert script._retry_backoff_seconds(1) == pytest.approx(1.0)
    assert script._retry_backoff_seconds(2) == pytest.approx(2.0)
    assert script._retry_backoff_seconds(10) == pytest.approx(4.0)


def test_collect_check_link_candidates_highlight_count_includes_non_highlight_children(script):
    docs = [
        {"id": "p1", "source_url": "https://x", "url": "https://rw/x", "location": "archive", "tags": {}},
        {"id": "h1", "parent_id": "p1", "category": "highlight"},
        {"id": "n1", "parent_id": "p1", "category": "note"},
        {"id": "u1", "parent_id": "p1"},
    ]
    row = script.collect_check_link_candidates(docs)[0]
    assert row["highlight_count"] == 3


def test_compute_child_counts_counts_all_child_categories(script):
    docs = [
        {"id": "p1"},
        {"id": "h1", "parent_id": "p1", "category": "highlight"},
        {"id": "n1", "parent_id": "p1", "category": "note"},
        {"id": "u1", "parent_id": "p1"},
    ]
    assert script.compute_child_counts(docs) == {"p1": 3}


def test_compute_child_counts_ignores_non_child_docs(script):
    docs = [
        {"id": "p1", "source_url": "https://example.com"},
        {"id": "p2", "category": "highlight"},
        {"id": "p3", "parent_id": ""},
        {"id": "p4", "parent_id": None},
    ]
    assert script.compute_child_counts(docs) == {}


def test_stats_table_includes_age_and_nonzero_locations(script):
    docs = [
        make_doc("1", location="new"),
        make_doc("2", location="new"),
        make_doc("3", location="later"),
        make_doc("4", location="archive"),
        make_doc("5", location="ignored"),
    ]
    meta = {"last_refresh": "2024-01-01T00:00:00+00:00"}
    now = datetime(2024, 1, 1, 1, 30, 0, tzinfo=timezone.utc)

    table = script.stats_table(docs, meta, now=now)
    rendered = render_table_text(table)

    assert "Total docs" in rendered
    assert "5" in rendered
    assert "Cache age" in rendered
    assert "1h 30m" in rendered
    assert "Inbox" in rendered
    assert "2" in rendered
    assert "Later" in rendered
    assert "1" in rendered
    assert "Archive" in rendered
    assert "Feed" not in rendered
    assert "Shortlist" not in rendered


def test_stats_table_all_locations_includes_zeros(script):
    docs = [make_doc("1", location="new")]
    meta = {"last_refresh": "2024-01-01T00:00:00+00:00"}

    table = script.stats_table(docs, meta, all_locations=True)
    rendered = render_table_text(table)

    assert "Feed" in rendered
    assert "Archive" in rendered
    assert "Later" in rendered
    assert "Shortlist" in rendered
    assert "Inbox" in rendered
    assert "0" in rendered
    assert "1" in rendered


def test_run_stats_prints_table(script, monkeypatch):
    monkeypatch.setattr(script, "setup_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "resolve_token", lambda: "token")
    monkeypatch.setattr(script, "refresh_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "load_meta", lambda: {"last_refresh": "2024-01-01T00:00:00+00:00"})
    monkeypatch.setattr(script, "load_cache", lambda: [make_doc("1"), make_doc("2")])

    printed = []
    monkeypatch.setattr(script.console, "print", lambda msg: printed.append(msg))

    args = script.parse_args(["stats"])
    script.run_stats(args)

    assert len(printed) == 1
    assert isinstance(printed[0], Table)
    assert printed[0].title == "Reader Document Stats"


def test_run_stats_no_refresh_skips_refresh(script, monkeypatch):
    monkeypatch.setattr(script, "setup_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(script, "resolve_token", lambda: "token")
    monkeypatch.setattr(script, "load_meta", lambda: {"last_refresh": "2024-01-01T00:00:00+00:00"})
    monkeypatch.setattr(script, "load_cache", lambda: [make_doc("1")])

    refresh_called = {"value": False}

    def _refresh(*args, **kwargs):
        refresh_called["value"] = True

    monkeypatch.setattr(script, "refresh_cache", _refresh)
    printed = []
    monkeypatch.setattr(script.console, "print", lambda msg: printed.append(msg))

    args = script.parse_args(["stats", "--no-refresh"])
    script.run_stats(args)

    assert not refresh_called["value"]
    assert len(printed) == 1
    assert isinstance(printed[0], Table)
    assert printed[0].title == "Reader Cache Stats"


def test_pick_keeper_by_highlights(script):
    docs = [make_doc("1", highlights=5), make_doc("2", highlights=2)]
    keeper, to_del, is_tie = script.pick_keeper(docs)
    assert keeper["id"] == "1"
    assert [d["id"] for d in to_del] == ["2"]
    assert not is_tie


def test_pick_keeper_by_tags(script):
    docs = [make_doc("1", tags=["a", "b"]), make_doc("2", tags=["a"])]
    keeper, _, is_tie = script.pick_keeper(docs)
    assert keeper["id"] == "1"
    assert not is_tie


def test_pick_keeper_by_location(script):
    docs = [make_doc("1", location="later"), make_doc("2", location="archive")]
    keeper, _, is_tie = script.pick_keeper(docs)
    assert keeper["id"] == "2"
    assert not is_tie


def test_pick_keeper_by_age(script):
    docs = [
        make_doc("1", created="2024-06-01T00:00:00Z"),
        make_doc("2", created="2023-01-01T00:00:00Z"),
    ]
    keeper, _, is_tie = script.pick_keeper(docs)
    assert keeper["id"] == "2"  # older wins


def test_pick_keeper_true_tie(script):
    docs = [
        make_doc("1", created="2024-01-01T00:00:00Z"),
        make_doc("2", created="2024-01-01T00:00:00Z"),
    ]
    _, _, is_tie = script.pick_keeper(docs)
    assert is_tie


def test_group_by_url_finds_duplicates(script):
    docs = [
        make_doc("1", url="https://example.com/a"),
        make_doc("2", url="https://example.com/a"),
        make_doc("3", url="https://example.com/b"),
    ]
    groups = script.group_by_url(docs)
    assert list(groups.keys()) == ["https://example.com/a"]
    assert len(groups["https://example.com/a"]) == 2


def test_group_by_url_case_normalized(script):
    docs = [
        make_doc("1", url="HTTPS://EXAMPLE.COM/page"),
        make_doc("2", url="https://example.com/page"),
    ]
    groups = script.group_by_url(docs)
    assert len(groups) == 1


def test_doc_label_collapses_multiline_title(script):
    doc = make_doc("1")
    doc["title"] = "Zed is 1.0\nZed is 1.0"
    label = script.doc_label(doc)
    assert "\n" not in label
    assert "Zed is 1.0 Zed is 1.0" in label


def test_deletion_table_collapses_multiline_cells(script):
    doc = make_doc("1", url="https://example.com/a")
    doc["title"] = "Line one\nLine two"
    table = script.deletion_table([doc])
    rendered = render_table_text(table)
    assert "Line one Line two" in rendered
