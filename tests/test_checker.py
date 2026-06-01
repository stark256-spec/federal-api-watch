"""Tests for endpoint health checking."""

import pytest
import respx
import httpx

from federal_api_watch.checker import CheckResult, check, _body_hash, _schema_sample
from federal_api_watch.registry import ApiEndpoint


def _api(slug: str = "test-api", url: str = "https://api.example.gov/v1/ping") -> ApiEndpoint:
    return ApiEndpoint(
        slug=slug,
        name="Test API",
        url=url,
        description="Test",
        agency="GSA",
        category="Test",
    )


def test_body_hash_is_16_chars():
    h = _body_hash(b"hello world")
    assert len(h) == 16


def test_body_hash_differs_for_different_content():
    assert _body_hash(b"aaa") != _body_hash(b"bbb")


def test_schema_sample_extracts_top_level_keys():
    body = b'{"results": [], "count": 0, "version": "1"}'
    keys = _schema_sample(body, "application/json")
    assert keys == ["count", "results", "version"]


def test_schema_sample_returns_none_for_non_json():
    assert _schema_sample(b"<html/>", "text/html") is None


@pytest.mark.asyncio
async def test_check_up_on_200():
    api = _api()
    with respx.mock:
        respx.get(api.url).mock(return_value=httpx.Response(200, json={"ok": True}))
        result = await check(api)
    assert result.status == "up"
    assert result.status_code == 200
    assert result.latency_ms is not None
    assert result.body_hash is not None
    assert result.error is None


@pytest.mark.asyncio
async def test_check_down_on_500():
    api = _api()
    with respx.mock:
        respx.get(api.url).mock(return_value=httpx.Response(500, text="error"))
        result = await check(api)
    assert result.status == "down"
    assert result.status_code == 500


@pytest.mark.asyncio
async def test_check_down_on_timeout():
    api = _api()
    with respx.mock:
        respx.get(api.url).mock(side_effect=httpx.TimeoutException("timed out"))
        result = await check(api)
    assert result.status == "down"
    assert result.status_code is None
    assert result.error == "timeout"


@pytest.mark.asyncio
async def test_check_captures_schema_sample():
    api = _api()
    with respx.mock:
        respx.get(api.url).mock(
            return_value=httpx.Response(200, json={"data": [], "meta": {}})
        )
        result = await check(api)
    assert result.schema_sample == ["data", "meta"]
