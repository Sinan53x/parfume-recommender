from pathlib import Path
import logging
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.application.pipelines.scrape_pipeline import ScrapePipeline
from app.config.logging import (
    SCRAPE_PARSE_FAILED,
    SCRAPE_RUN_END,
    SCRAPE_RUN_START,
    SCRAPE_URL_FAILED,
    SCRAPE_URL_FETCHED,
)
from app.domain.models.perfume import Perfume
from app.infrastructure.scraping.client import ScrapeHttpResponse


class _FakeHttpClient:
    def __init__(self, pages: dict[str, str], failing_urls: set[str] | None = None) -> None:
        self.pages = pages
        self.failing_urls = failing_urls or set()

    def fetch(self, url: str) -> ScrapeHttpResponse:
        if url in self.failing_urls:
            raise RuntimeError("fetch failed")
        return ScrapeHttpResponse(url=url, status_code=200, text=self.pages[url], headers={})


class _FakeAccessGuard:
    def enforce(self, url: str) -> None:
        return None


class _FakePerfumeRepo:
    def __init__(self) -> None:
        self.saved: list[Perfume] = []

    def upsert_perfume(self, perfume: Perfume) -> None:
        self.saved.append(perfume)


def test_scrape_pipeline_logs_start_url_fetch_and_end(caplog) -> None:  # noqa: ANN001
    pages = {
        "https://vicioso.example/collections/all": """
            <article><a href=\"/products/amber-night\">Amber Night</a></article>
        """,
        "https://vicioso.example/products/amber-night": """
            <meta name=\"description\" content=\"Warm floral profile.\" />
            <div>Top Notes: Bergamot</div>
            <div>Heart Notes: Rose</div>
            <div>Base Notes: Vanilla</div>
        """,
    }
    logger = logging.getLogger("test.scrape_pipeline.logging")
    pipeline = ScrapePipeline(
        http_client=_FakeHttpClient(pages),
        access_guard=_FakeAccessGuard(),
        perfume_repository=_FakePerfumeRepo(),
        base_url="https://vicioso.example",
        logger=logger,
    )

    with caplog.at_level(logging.INFO, logger=logger.name):
        pipeline.run(seed_listing_urls=("/collections/all",))

    events = [record.event for record in caplog.records if hasattr(record, "event")]
    assert SCRAPE_RUN_START in events
    assert SCRAPE_URL_FETCHED in events
    assert SCRAPE_RUN_END in events

    run_end = next(record for record in caplog.records if getattr(record, "event", "") == SCRAPE_RUN_END)
    assert run_end.scraped_count == 1
    assert run_end.discovered_product_count == 1
    assert run_end.success_rate == 1.0


def test_scrape_pipeline_logs_fetch_and_parse_failures(caplog) -> None:  # noqa: ANN001
    pages = {
        "https://vicioso.example/collections/all": """
            <article><a href=\"/products/amber-night\">Amber Night</a></article>
        """,
    }
    logger = logging.getLogger("test.scrape_pipeline.logging.failures")
    pipeline = ScrapePipeline(
        http_client=_FakeHttpClient(pages, failing_urls={"https://vicioso.example/products/amber-night"}),
        access_guard=_FakeAccessGuard(),
        perfume_repository=_FakePerfumeRepo(),
        base_url="https://vicioso.example",
        logger=logger,
    )

    with caplog.at_level(logging.WARNING, logger=logger.name):
        pipeline.run(seed_listing_urls=("/collections/all",))

    events = [record.event for record in caplog.records if hasattr(record, "event")]
    assert SCRAPE_URL_FAILED in events
    assert SCRAPE_PARSE_FAILED in events

    parse_fail = next(
        record for record in caplog.records if getattr(record, "event", "") == SCRAPE_PARSE_FAILED
    )
    assert parse_fail.stage == "product"
    assert parse_fail.url == "https://vicioso.example/products/amber-night"
