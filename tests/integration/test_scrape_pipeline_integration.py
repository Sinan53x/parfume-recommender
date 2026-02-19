from pathlib import Path
import logging
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.application.pipelines.scrape_pipeline import ScrapePipeline
from app.config.logging import SCRAPE_RUN_END
from app.infrastructure.persistence.sqlite.perfume_repo_sqlite import PerfumeRepositorySqlite
from app.infrastructure.scraping.client import ScrapeHttpResponse


class _FakeHttpClient:
    def __init__(self, pages: dict[str, str], failing_urls: set[str] | None = None) -> None:
        self.pages = pages
        self.failing_urls = failing_urls or set()

    def fetch(self, url: str) -> ScrapeHttpResponse:
        if url in self.failing_urls:
            raise RuntimeError("fetch failed")
        return ScrapeHttpResponse(url=url, status_code=200, text=self.pages[url], headers={})


class _AllowAllGuard:
    def enforce(self, url: str) -> None:
        return None


def test_scrape_pipeline_integration_persists_perfumes_and_logs_success_rate(caplog) -> None:  # noqa: ANN001
    connection = sqlite3.connect(":memory:")
    repo = PerfumeRepositorySqlite(connection)
    repo.initialize_schema()

    pages = {
        "https://vicioso.example/collections/all": """
            <article><a href=\"/products/amber-night\">Amber Night</a><span>€59,90</span></article>
            <article><a href=\"/products/fresh-dawn\">Fresh Dawn</a><span>49 EUR</span></article>
        """,
        "https://vicioso.example/products/amber-night": """
            <meta name=\"description\" content=\"Warm floral profile.\" />
            <div>Top Notes: Bergamot</div>
            <div>Heart Notes: Rose</div>
            <div>Base Notes: Vanilla</div>
            <div>Duftfamilie: Blumig</div>
            <img src=\"/images/amber.jpg\" />
        """,
    }
    logger = logging.getLogger("test.integration.scrape_pipeline")
    pipeline = ScrapePipeline(
        http_client=_FakeHttpClient(pages, {"https://vicioso.example/products/fresh-dawn"}),
        access_guard=_AllowAllGuard(),
        perfume_repository=repo,
        base_url="https://vicioso.example",
        logger=logger,
    )

    with caplog.at_level(logging.INFO, logger=logger.name):
        result = pipeline.run(seed_listing_urls=("/collections/all",))

    run_end = next(record for record in caplog.records if getattr(record, "event", "") == SCRAPE_RUN_END)
    assert run_end.discovered_product_count == 2
    assert run_end.scraped_count == 1
    assert run_end.success_rate == 0.5
    assert result.scraped_count == 1
    assert result.failed_product_urls == ("https://vicioso.example/products/fresh-dawn",)

    stored = repo.list_perfumes()
    assert len(stored) == 1
    assert stored[0].perfume_id == "amber-night"
    assert stored[0].scent_families == ("Floral",)
