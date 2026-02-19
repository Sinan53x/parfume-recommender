from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable
from urllib import error, request


@dataclass(frozen=True)
class ScrapeHttpResponse:
    url: str
    status_code: int
    text: str
    headers: dict[str, str]


class ScrapeHttpClient:
    def __init__(
        self,
        timeout_seconds: float = 20.0,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
        backoff_multiplier: float = 2.0,
        user_agent: str = "PerfumeRecommenderBot/1.0",
        sleep_func: Callable[[float], None] = time.sleep,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.backoff_multiplier = backoff_multiplier
        self.user_agent = user_agent
        self.sleep_func = sleep_func

    def fetch(self, url: str, extra_headers: dict[str, str] | None = None) -> ScrapeHttpResponse:
        headers = {"User-Agent": self.user_agent}
        if extra_headers:
            headers.update(extra_headers)

        attempt = 0
        backoff = self.backoff_seconds

        while True:
            try:
                return self._fetch_once(url=url, headers=headers)
            except error.HTTPError as exc:
                if not _should_retry_status(exc.code) or attempt >= self.max_retries:
                    raise
            except (error.URLError, TimeoutError):
                if attempt >= self.max_retries:
                    raise

            self.sleep_func(backoff)
            attempt += 1
            backoff *= self.backoff_multiplier

    def _fetch_once(self, url: str, headers: dict[str, str]) -> ScrapeHttpResponse:
        req = request.Request(url=url, headers=headers)
        with request.urlopen(req, timeout=self.timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace")
            status_code = int(response.getcode())
            response_headers = {key: value for key, value in response.headers.items()}
            return ScrapeHttpResponse(
                url=response.geturl(),
                status_code=status_code,
                text=body,
                headers=response_headers,
            )


def _should_retry_status(status_code: int) -> bool:
    return status_code in {429, 500, 502, 503, 504}
