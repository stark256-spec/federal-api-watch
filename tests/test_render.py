"""Tests for status page, RSS, and badge rendering."""

from pathlib import Path

from federal_api_watch.render import render_all, render_badge, render_rss, render_summary_badge
from federal_api_watch.registry import REGISTRY_BY_SLUG


def _state(slug: str = "test-api", status: str = "up", uptime: float = 99.9) -> dict:
    return {
        "slug": slug,
        "name": "Test API",
        "agency": "GSA",
        "description": "A test endpoint.",
        "current_status": status,
        "current_latency_ms": 120,
        "last_checked": "2024-06-01T12:00:00+00:00",
        "uptime_7d": uptime,
        "history": [],
        "changelog": [],
    }


def test_render_all_creates_expected_files(tmp_path: Path):
    states = [_state("data-gov-catalog"), _state("federal-register")]
    docs = tmp_path / "docs"
    render_all(states, REGISTRY_BY_SLUG, docs)
    assert (docs / "index.html").exists()
    assert (docs / "feed.xml").exists()
    assert (docs / "badge" / "summary.json").exists()
    assert (docs / "badge" / "data-gov-catalog.json").exists()


def test_html_contains_api_name(tmp_path: Path):
    states = [_state("data-gov-catalog")]
    docs = tmp_path / "docs"
    render_all(states, REGISTRY_BY_SLUG, docs)
    html = (docs / "index.html").read_text()
    assert "Data.gov" in html


def test_html_shows_all_up_when_everything_is_up(tmp_path: Path):
    states = [_state(status="up"), _state("federal-register", status="up")]
    docs = tmp_path / "docs"
    render_all(states, REGISTRY_BY_SLUG, docs)
    html = (docs / "index.html").read_text()
    assert "All systems operational" in html


def test_html_shows_down_count_when_api_is_down(tmp_path: Path):
    states = [_state(status="up"), _state("federal-register", status="down")]
    docs = tmp_path / "docs"
    render_all(states, REGISTRY_BY_SLUG, docs)
    html = (docs / "index.html").read_text()
    assert "1 API" in html


def test_badge_green_when_up(tmp_path: Path):
    import json
    path = tmp_path / "badge.json"
    render_badge(_state(status="up"), path)
    badge = json.loads(path.read_text())
    assert badge["message"] == "up"
    assert badge["color"] == "brightgreen"


def test_badge_red_when_down(tmp_path: Path):
    import json
    path = tmp_path / "badge.json"
    render_badge(_state(status="down"), path)
    badge = json.loads(path.read_text())
    assert badge["color"] == "red"


def test_summary_badge_all_up(tmp_path: Path):
    import json
    path = tmp_path / "summary.json"
    render_summary_badge([_state(), _state("b")], path)
    badge = json.loads(path.read_text())
    assert badge["message"] == "all up"
    assert badge["color"] == "brightgreen"


def test_rss_includes_changelog_entries(tmp_path: Path):
    state = _state()
    state["changelog"] = [
        {"timestamp": "2024-06-01T10:00:00Z", "kind": "status_change", "before": "up", "after": "down"},
    ]
    path = tmp_path / "feed.xml"
    render_rss([state], REGISTRY_BY_SLUG, path)
    xml = path.read_text()
    assert "<item>" in xml
    assert "status_change" not in xml
    assert "up" in xml
