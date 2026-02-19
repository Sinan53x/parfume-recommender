from pathlib import Path
import sys
from urllib import error

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.infrastructure.scraping.client import ScrapeHttpClient


class _FakeResponse:
    def __init__(self, url: str, body: str, status: int = 200) -> None:
        self._url = url
        self._body = body.encode("utf-8")
        self._status = status
        self.headers = {"Content-Type": "text/html"}

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return self._body

    def getcode(self) -> int:
        return self._status

    def geturl(self) -> str:
        return self._url


def test_fetch_returns_response_on_first_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout):  # noqa: ANN001
        assert req.full_url == "https://example.com/products"
        assert timeout == 5.0
        assert req.headers["User-agent"] == "UnitTestBot/1.0"
        return _FakeResponse(url=req.full_url, body="<html>ok</html>")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = ScrapeHttpClient(timeout_seconds=5.0, user_agent="UnitTestBot/1.0")

    response = client.fetch("https://example.com/products")

    assert response.status_code == 200
    assert response.url == "https://example.com/products"
    assert response.text == "<html>ok</html>"
    assert response.headers["Content-Type"] == "text/html"


def test_fetch_retries_on_transient_errors_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    def fake_urlopen(req, timeout):  # noqa: ANN001
        calls["count"] += 1
        if calls["count"] < 3:
            raise error.URLError("temporary failure")
        return _FakeResponse(url=req.full_url, body="done")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = ScrapeHttpClient(
        max_retries=3,
        backoff_seconds=0.5,
        backoff_multiplier=2.0,
        sleep_func=fake_sleep,
    )

    response = client.fetch("https://example.com/retry")

    assert response.text == "done"
    assert calls["count"] == 3
    assert slept == [0.5, 1.0]


def test_fetch_does_not_retry_non_retriable_http_status(monkeypatch: pytest.MonkeyPatch) -> None:
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    def fake_urlopen(req, timeout):  # noqa: ANN001
        raise error.HTTPError(req.full_url, 404, "Not Found", hdrs=None, fp=None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = ScrapeHttpClient(max_retries=5, sleep_func=fake_sleep)

    with pytest.raises(error.HTTPError):
        client.fetch("https://example.com/missing")

    assert slept == []


def test_fetch_retries_and_raises_after_max_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    def fake_urlopen(req, timeout):  # noqa: ANN001
        calls["count"] += 1
        raise error.HTTPError(req.full_url, 503, "Service Unavailable", hdrs=None, fp=None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = ScrapeHttpClient(max_retries=2, backoff_seconds=1.0, sleep_func=fake_sleep)

    with pytest.raises(error.HTTPError):
        client.fetch("https://example.com/unavailable")

    assert calls["count"] == 3
    assert slept == [1.0, 2.0]
