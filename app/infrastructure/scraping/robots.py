from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Callable
from urllib import error, request, robotparser
from urllib.parse import urlparse


def _origin_from_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _domain_from_url(url: str) -> str:
    return urlparse(url).netloc


class RobotsTxtPolicy:
    def __init__(
        self,
        user_agent: str = "PerfumeRecommenderBot/1.0",
        robots_fetcher: Callable[[str], str] | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.robots_fetcher = robots_fetcher or _default_robots_fetcher
        self._parsers: dict[str, robotparser.RobotFileParser | None] = {}

    def can_fetch(self, url: str) -> bool:
        origin = _origin_from_url(url)
        parser = self._parsers.get(origin)
        if parser is None and origin not in self._parsers:
            parser = _build_robot_parser(origin, self.robots_fetcher)
            self._parsers[origin] = parser

        if parser is None:
            return True

        return parser.can_fetch(self.user_agent, url)


@dataclass
class DomainRateLimiter:
    min_interval_seconds: float = 1.0
    time_func: Callable[[], float] = time.monotonic
    sleep_func: Callable[[float], None] = time.sleep
    _last_seen_at: dict[str, float] = field(default_factory=dict)

    def wait_for_slot(self, url: str) -> None:
        domain = _domain_from_url(url)
        now = self.time_func()
        last_seen = self._last_seen_at.get(domain)

        if last_seen is not None:
            elapsed = now - last_seen
            if elapsed < self.min_interval_seconds:
                self.sleep_func(self.min_interval_seconds - elapsed)

        self._last_seen_at[domain] = self.time_func()


@dataclass
class ScrapeAccessGuard:
    robots_policy: RobotsTxtPolicy = field(default_factory=RobotsTxtPolicy)
    rate_limiter: DomainRateLimiter = field(default_factory=DomainRateLimiter)

    def enforce(self, url: str) -> None:
        if not self.robots_policy.can_fetch(url):
            raise PermissionError(f"robots.txt forbids scraping: {url}")

        self.rate_limiter.wait_for_slot(url)


def _build_robot_parser(
    origin: str,
    robots_fetcher: Callable[[str], str],
) -> robotparser.RobotFileParser | None:
    try:
        robots_text = robots_fetcher(origin)
    except OSError:
        return None

    parser = robotparser.RobotFileParser()
    parser.set_url(f"{origin}/robots.txt")
    parser.parse(robots_text.splitlines())
    return parser


def _default_robots_fetcher(origin: str) -> str:
    robots_url = f"{origin}/robots.txt"
    req = request.Request(robots_url, headers={"User-Agent": "PerfumeRecommenderBot/1.0"})
    try:
        with request.urlopen(req, timeout=10.0) as response:
            return response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        if exc.code == 404:
            return ""
        raise
