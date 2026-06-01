"""Read and write per-API status JSON files in data/status/."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from federal_api_watch.checker import CheckResult

_MAX_HISTORY = 672  # 7 days × 96 polls/day (every 15 min)


def status_path(data_dir: Path, slug: str) -> Path:
    return data_dir / "status" / f"{slug}.json"


def load_status(data_dir: Path, slug: str) -> dict[str, Any]:
    path = status_path(data_dir, slug)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"slug": slug, "history": [], "changelog": []}


def save_status(data_dir: Path, result: CheckResult, previous: dict[str, Any]) -> dict[str, Any]:
    history: list[dict[str, Any]] = previous.get("history", [])
    changelog: list[dict[str, Any]] = previous.get("changelog", [])

    entry = asdict(result)
    history.append(entry)
    history = history[-_MAX_HISTORY:]

    # detect schema change
    if len(history) >= 2:
        prev = history[-2]
        curr = history[-1]
        if (
            prev.get("schema_sample") is not None
            and curr.get("schema_sample") is not None
            and prev["schema_sample"] != curr["schema_sample"]
        ):
            changelog.append({
                "timestamp": curr["timestamp"],
                "kind": "schema_change",
                "before": prev["schema_sample"],
                "after": curr["schema_sample"],
            })
        elif prev.get("body_hash") != curr.get("body_hash") and curr.get("status") == "up":
            pass  # body hash changes too often to log individually

        # detect status transitions
        if prev.get("status") != curr.get("status"):
            changelog.append({
                "timestamp": curr["timestamp"],
                "kind": "status_change",
                "before": prev.get("status"),
                "after": curr.get("status"),
            })

    uptime_pct = _uptime_pct(history)

    state = {
        "slug": result.slug,
        "name": previous.get("name", result.slug),
        "current_status": result.status,
        "current_latency_ms": result.latency_ms,
        "last_checked": result.timestamp,
        "uptime_7d": uptime_pct,
        "history": history,
        "changelog": changelog[-200:],
    }

    path = status_path(data_dir, result.slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def _uptime_pct(history: list[dict[str, Any]]) -> float:
    if not history:
        return 100.0
    up = sum(1 for h in history if h.get("status") == "up")
    return round(up / len(history) * 100, 2)


def load_all_status(data_dir: Path, slugs: list[str]) -> list[dict[str, Any]]:
    return [load_status(data_dir, slug) for slug in slugs]
