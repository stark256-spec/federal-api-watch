"""CLI entry point: poll, render, or both."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from federal_api_watch.checker import check
from federal_api_watch.registry import REGISTRY, REGISTRY_BY_SLUG
from federal_api_watch.render import render_all
from federal_api_watch.store import load_all_status, load_status, save_status

_DATA_DIR = Path("data")
_DOCS_DIR = Path("docs")


async def _poll_all() -> None:
    import httpx

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [check(api, client=client) for api in REGISTRY]
        results = await asyncio.gather(*tasks)

    for result in results:
        prev = load_status(_DATA_DIR, result.slug)
        prev["name"] = REGISTRY_BY_SLUG[result.slug].name
        state = save_status(_DATA_DIR, result, prev)
        status_icon = {"up": "✓", "degraded": "~", "down": "✗"}.get(state["current_status"], "?")
        latency = f"{state['current_latency_ms']}ms" if state["current_latency_ms"] else "timeout"
        print(f"  {status_icon} {result.slug:<35} {state['current_status']:<10} {latency}")


def _render() -> None:
    slugs = [a.slug for a in REGISTRY]
    states = load_all_status(_DATA_DIR, slugs)
    for state in states:
        slug = state["slug"]
        if api := REGISTRY_BY_SLUG.get(slug):
            state["name"] = api.name
    render_all(states, REGISTRY_BY_SLUG, _DOCS_DIR)
    print(f"Rendered {len(states)} APIs → {_DOCS_DIR}/")


def main() -> None:
    args = sys.argv[1:]
    command = args[0] if args else "all"

    if command == "poll":
        print("Polling all APIs …")
        asyncio.run(_poll_all())
    elif command == "render":
        _render()
    elif command in ("all", ""):
        print("Polling all APIs …")
        asyncio.run(_poll_all())
        _render()
    else:
        print(f"Usage: federal-api-watch [poll|render|all]", file=sys.stderr)
        sys.exit(1)
