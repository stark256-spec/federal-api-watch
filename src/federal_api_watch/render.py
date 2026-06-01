"""Generate status page HTML, RSS feed, and shields.io badge JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, BaseLoader

_STATUS_COLOR = {"up": "#2da44e", "degraded": "#e3a000", "down": "#cf222e"}
_STATUS_LABEL = {"up": "up", "degraded": "degraded", "down": "down"}

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Federal API Status</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="alternate" type="application/rss+xml" title="Federal API Changelog" href="feed.xml">
</head>
<body class="bg-gray-50 text-gray-900 font-sans">
  <div class="max-w-4xl mx-auto px-4 py-10">
    <div class="flex items-center justify-between mb-2">
      <h1 class="text-2xl font-bold">🇺🇸 Federal API Status</h1>
      <a href="feed.xml" class="text-sm text-blue-600 hover:underline">RSS feed</a>
    </div>
    <p class="text-gray-500 text-sm mb-8">Updated {{ generated_at }} · <a class="text-blue-600 hover:underline" href="https://github.com/stark256-spec/federal-api-watch">GitHub</a></p>

    <div class="mb-6 p-4 rounded-lg border {% if all_up %}bg-green-50 border-green-200{% else %}bg-red-50 border-red-200{% endif %}">
      {% if all_up %}
        <span class="font-semibold text-green-700">✓ All systems operational</span>
      {% else %}
        <span class="font-semibold text-red-700">⚠ {{ down_count }} API{{ 's' if down_count != 1 }} down or degraded</span>
      {% endif %}
    </div>

    {% for cat, apis in by_category.items() %}
    <h2 class="text-lg font-semibold mt-8 mb-3 text-gray-700">{{ cat }}</h2>
    <div class="space-y-2">
      {% for api in apis %}
      <div class="flex items-center justify-between bg-white rounded-lg border border-gray-200 px-4 py-3">
        <div class="flex-1 min-w-0 mr-4">
          <div class="flex items-center gap-2">
            <span class="font-medium text-sm">{{ api.name }}</span>
            <span class="text-xs text-gray-400">{{ api.agency }}</span>
          </div>
          <div class="text-xs text-gray-400 truncate mt-0.5">{{ api.description }}</div>
        </div>
        <div class="flex items-center gap-4 shrink-0 text-right">
          <div class="hidden sm:block">
            <div class="text-xs text-gray-400">7d uptime</div>
            <div class="text-sm font-mono font-medium {% if api.uptime_7d >= 99 %}text-green-600{% elif api.uptime_7d >= 95 %}text-yellow-600{% else %}text-red-600{% endif %}">{{ api.uptime_7d }}%</div>
          </div>
          {% if api.current_latency_ms %}
          <div class="hidden sm:block">
            <div class="text-xs text-gray-400">latency</div>
            <div class="text-sm font-mono {% if api.current_latency_ms < 500 %}text-green-600{% elif api.current_latency_ms < 2000 %}text-yellow-600{% else %}text-red-600{% endif %}">{{ api.current_latency_ms }}ms</div>
          </div>
          {% endif %}
          <div>
            <span class="inline-block px-2 py-1 rounded text-xs font-semibold text-white" style="background:{{ status_color(api.current_status) }}">{{ api.current_status }}</span>
          </div>
          <a href="badge/{{ api.slug }}.json" class="text-xs text-blue-600 hover:underline hidden md:block">badge</a>
        </div>
      </div>
      {% if api.changelog %}
      <div class="ml-4 mb-2">
        {% for entry in api.changelog[-3:]|reverse %}
        <div class="text-xs text-gray-500 flex gap-2">
          <span class="text-gray-400">{{ entry.timestamp[:10] }}</span>
          {% if entry.kind == 'schema_change' %}
          <span class="text-orange-600 font-medium">schema changed</span>
          <span>{{ entry.before }} → {{ entry.after }}</span>
          {% elif entry.kind == 'status_change' %}
          <span class="{% if entry.after == 'up' %}text-green-600{% else %}text-red-600{% endif %} font-medium">{{ entry.before }} → {{ entry.after }}</span>
          {% endif %}
        </div>
        {% endfor %}
      </div>
      {% endif %}
      {% endfor %}
    </div>
    {% endfor %}

    <div class="mt-12 pt-6 border-t border-gray-200 text-xs text-gray-400">
      <p>Polls every 15 minutes via GitHub Actions. Data stored as JSON in the repo. <a class="text-blue-600 hover:underline" href="https://github.com/stark256-spec/federal-api-watch">Embed a badge</a> in your README.</p>
    </div>
  </div>
</body>
</html>
"""

_RSS_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Federal API Changelog</title>
    <link>https://stark256-spec.github.io/federal-api-watch/</link>
    <description>Uptime and schema change events for U.S. federal government APIs.</description>
    <language>en-us</language>
    <atom:link href="https://stark256-spec.github.io/federal-api-watch/feed.xml" rel="self" type="application/rss+xml"/>
    {% for item in items %}
    <item>
      <title>{{ item.title }}</title>
      <link>https://stark256-spec.github.io/federal-api-watch/</link>
      <description>{{ item.description }}</description>
      <pubDate>{{ item.pub_date }}</pubDate>
      <guid isPermaLink="false">{{ item.guid }}</guid>
    </item>
    {% endfor %}
  </channel>
</rss>
"""


def _env() -> Environment:
    e = Environment(loader=BaseLoader(), autoescape=True)
    e.globals["status_color"] = lambda s: _STATUS_COLOR.get(s, "#666")
    return e


def _group_by_category(
    states: list[dict[str, Any]],
    registry_map: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for state in states:
        slug = state["slug"]
        api = registry_map.get(slug)
        cat = api.category if api else "Other"
        enriched = dict(state)
        enriched["name"] = api.name if api else slug
        enriched["agency"] = api.agency if api else ""
        enriched["description"] = api.description if api else ""
        grouped.setdefault(cat, []).append(enriched)
    return dict(sorted(grouped.items()))


def render_html(
    states: list[dict[str, Any]],
    registry_map: dict[str, Any],
    output_path: Path,
) -> None:
    by_category = _group_by_category(states, registry_map)
    all_statuses = [s.get("current_status") for s in states]
    down_count = sum(1 for s in all_statuses if s in ("down", "degraded"))

    ctx = {
        "by_category": by_category,
        "all_up": down_count == 0,
        "down_count": down_count,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    html = _env().from_string(_HTML_TEMPLATE).render(**ctx)
    output_path.write_text(html, encoding="utf-8")


def render_rss(
    states: list[dict[str, Any]],
    registry_map: dict[str, Any],
    output_path: Path,
) -> None:
    items: list[dict[str, str]] = []
    for state in states:
        slug = state["slug"]
        api = registry_map.get(slug)
        name = api.name if api else slug
        for entry in state.get("changelog", [])[-10:]:
            kind = entry.get("kind", "")
            ts = entry.get("timestamp", "")
            if kind == "schema_change":
                title = f"{name}: schema changed"
                desc = f"Top-level keys changed from {entry.get('before')} to {entry.get('after')}"
            elif kind == "status_change":
                title = f"{name}: {entry.get('before')} → {entry.get('after')}"
                desc = f"{name} changed status from {entry.get('before')} to {entry.get('after')}"
            else:
                continue
            items.append({
                "title": title,
                "description": desc,
                "pub_date": ts,
                "guid": f"{slug}-{ts}",
            })

    items.sort(key=lambda i: i["pub_date"], reverse=True)
    xml = _env().from_string(_RSS_TEMPLATE).render(items=items[:50])
    output_path.write_text(xml, encoding="utf-8")


def render_badge(state: dict[str, Any], output_path: Path) -> None:
    status = state.get("current_status", "unknown")
    color = {"up": "brightgreen", "degraded": "yellow", "down": "red"}.get(status, "lightgrey")
    badge = {
        "schemaVersion": 1,
        "label": state.get("name", state["slug"]),
        "message": status,
        "color": color,
    }
    output_path.write_text(json.dumps(badge), encoding="utf-8")


def render_summary_badge(states: list[dict[str, Any]], output_path: Path) -> None:
    down = [s for s in states if s.get("current_status") in ("down", "degraded")]
    if not down:
        msg, color = "all up", "brightgreen"
    elif len(down) == 1:
        msg, color = "1 down", "red"
    else:
        msg, color = f"{len(down)} down", "red"
    badge = {"schemaVersion": 1, "label": "federal APIs", "message": msg, "color": color}
    output_path.write_text(json.dumps(badge), encoding="utf-8")


def render_all(
    states: list[dict[str, Any]],
    registry_map: dict[str, Any],
    docs_dir: Path,
) -> None:
    docs_dir.mkdir(parents=True, exist_ok=True)
    badge_dir = docs_dir / "badge"
    badge_dir.mkdir(exist_ok=True)

    render_html(states, registry_map, docs_dir / "index.html")
    render_rss(states, registry_map, docs_dir / "feed.xml")
    render_summary_badge(states, docs_dir / "badge" / "summary.json")

    for state in states:
        render_badge(state, badge_dir / f"{state['slug']}.json")
