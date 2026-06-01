"""Probe a single API endpoint and return a health result."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any

import httpx

from federal_api_watch.registry import ApiEndpoint


@dataclass
class CheckResult:
    slug: str
    timestamp: str
    status: str          # "up" | "degraded" | "down"
    status_code: int | None
    latency_ms: int | None
    body_hash: str | None
    schema_sample: Any   # top-level keys or first-level structure
    error: str | None


def _body_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]


def _schema_sample(content: bytes, content_type: str) -> Any:
    """Extract a lightweight schema fingerprint — top-level keys for JSON."""
    if "json" not in content_type:
        return None
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return sorted(data.keys())
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return sorted(data[0].keys())
        return type(data).__name__
    except Exception:
        return None


async def check(api: ApiEndpoint, *, client: httpx.AsyncClient | None = None) -> CheckResult:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()

    async def _probe(c: httpx.AsyncClient) -> CheckResult:
        start = time.monotonic()
        try:
            if api.headers.get("Content-Type") == "application/json":
                # grants.gov needs a POST
                r = await c.post(
                    api.url,
                    json={"rows": 1, "keyword": "health"},
                    headers=api.headers,
                    timeout=api.timeout,
                )
            else:
                r = await c.get(
                    api.url,
                    headers=api.headers,
                    timeout=api.timeout,
                )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            content = r.content
            content_type = r.headers.get("content-type", "")
            bh = _body_hash(content)
            sample = _schema_sample(content, content_type)

            if r.status_code == api.expected_status:
                status = "degraded" if elapsed_ms > 5000 else "up"
            else:
                status = "down"

            return CheckResult(
                slug=api.slug,
                timestamp=now,
                status=status,
                status_code=r.status_code,
                latency_ms=elapsed_ms,
                body_hash=bh,
                schema_sample=sample,
                error=None,
            )
        except httpx.TimeoutException:
            return CheckResult(
                slug=api.slug,
                timestamp=now,
                status="down",
                status_code=None,
                latency_ms=None,
                body_hash=None,
                schema_sample=None,
                error="timeout",
            )
        except Exception as exc:
            return CheckResult(
                slug=api.slug,
                timestamp=now,
                status="down",
                status_code=None,
                latency_ms=None,
                body_hash=None,
                schema_sample=None,
                error=str(exc)[:200],
            )

    if client is not None:
        return await _probe(client)
    async with httpx.AsyncClient(follow_redirects=True) as c:
        return await _probe(c)
