"""Tests for status store — history, uptime, changelog."""

from pathlib import Path

from federal_api_watch.checker import CheckResult
from federal_api_watch.store import _uptime_pct, load_status, save_status


def _result(slug: str = "test", status: str = "up", schema: list | None = None) -> CheckResult:
    return CheckResult(
        slug=slug,
        timestamp="2024-06-01T12:00:00+00:00",
        status=status,
        status_code=200 if status != "down" else 500,
        latency_ms=120,
        body_hash="abc123",
        schema_sample=schema or ["count", "results"],
        error=None,
    )


def test_save_creates_status_file(tmp_path: Path):
    result = _result()
    save_status(tmp_path, result, {"history": [], "changelog": []})
    assert (tmp_path / "status" / "test.json").exists()


def test_load_returns_empty_for_missing_slug(tmp_path: Path):
    state = load_status(tmp_path, "nonexistent")
    assert state["slug"] == "nonexistent"
    assert state["history"] == []


def test_history_accumulates(tmp_path: Path):
    prev = {"history": [], "changelog": []}
    for _ in range(3):
        r = _result()
        prev = save_status(tmp_path, r, prev)
    assert len(prev["history"]) == 3


def test_uptime_pct_all_up():
    history = [{"status": "up"}, {"status": "up"}, {"status": "up"}]
    assert _uptime_pct(history) == 100.0


def test_uptime_pct_mixed():
    history = [{"status": "up"}, {"status": "down"}, {"status": "up"}, {"status": "up"}]
    assert _uptime_pct(history) == 75.0


def test_uptime_pct_empty():
    assert _uptime_pct([]) == 100.0


def test_changelog_records_status_transition(tmp_path: Path):
    prev = {"history": [], "changelog": []}
    up = _result(status="up")
    prev = save_status(tmp_path, up, prev)
    down = _result(status="down")
    down.timestamp = "2024-06-01T13:00:00+00:00"
    prev = save_status(tmp_path, down, prev)
    status_events = [e for e in prev["changelog"] if e["kind"] == "status_change"]
    assert any(e["after"] == "down" for e in status_events)


def test_changelog_records_schema_change(tmp_path: Path):
    prev = {"history": [], "changelog": []}
    r1 = _result(schema=["count", "results"])
    prev = save_status(tmp_path, r1, prev)
    r2 = _result(schema=["count", "results", "version"])
    r2.timestamp = "2024-06-01T13:00:00+00:00"
    prev = save_status(tmp_path, r2, prev)
    schema_events = [e for e in prev["changelog"] if e["kind"] == "schema_change"]
    assert len(schema_events) == 1
    assert "version" in schema_events[0]["after"]
