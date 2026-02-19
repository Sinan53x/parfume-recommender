from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.infrastructure.scraping.robots import (
    DomainRateLimiter,
    RobotsTxtPolicy,
    ScrapeAccessGuard,
)


def test_robots_policy_allows_and_blocks_by_rule() -> None:
    def fake_fetcher(origin: str) -> str:
        assert origin == "https://vicioso.example"
        return "User-agent: *\nDisallow: /private\nAllow: /"

    policy = RobotsTxtPolicy(user_agent="PerfumeRecommenderBot", robots_fetcher=fake_fetcher)

    assert policy.can_fetch("https://vicioso.example/products/amber-night") is True
    assert policy.can_fetch("https://vicioso.example/private/internal") is False


def test_robots_policy_allows_when_robots_unavailable() -> None:
    def failing_fetcher(origin: str) -> str:
        raise OSError("network unavailable")

    policy = RobotsTxtPolicy(user_agent="PerfumeRecommenderBot", robots_fetcher=failing_fetcher)

    assert policy.can_fetch("https://vicioso.example/products/amber-night") is True


def test_domain_rate_limiter_waits_for_same_domain_only() -> None:
    now = {"value": 0.0}
    sleeps: list[float] = []

    def fake_time() -> float:
        return now["value"]

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now["value"] += seconds

    limiter = DomainRateLimiter(
        min_interval_seconds=1.0,
        time_func=fake_time,
        sleep_func=fake_sleep,
    )

    limiter.wait_for_slot("https://vicioso.example/a")
    limiter.wait_for_slot("https://vicioso.example/b")
    limiter.wait_for_slot("https://other.example/a")

    assert sleeps == [1.0]


def test_scrape_access_guard_raises_on_robots_block() -> None:
    policy = RobotsTxtPolicy(
        user_agent="PerfumeRecommenderBot",
        robots_fetcher=lambda origin: "User-agent: *\nDisallow: /",
    )
    limiter = DomainRateLimiter(min_interval_seconds=1.0, time_func=lambda: 0.0, sleep_func=lambda _: None)
    guard = ScrapeAccessGuard(robots_policy=policy, rate_limiter=limiter)

    with pytest.raises(PermissionError, match="robots.txt forbids"):
        guard.enforce("https://vicioso.example/products/amber-night")
