from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.application.pipelines.scrape_pipeline import ScrapePipeline
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
    def __init__(self, blocked_urls: set[str] | None = None) -> None:
        self.blocked_urls = blocked_urls or set()
        self.checked_urls: list[str] = []

    def enforce(self, url: str) -> None:
        self.checked_urls.append(url)
        if url in self.blocked_urls:
            raise PermissionError("blocked by robots")


class _FakePerfumeRepo:
    def __init__(self) -> None:
        self.saved: list[Perfume] = []

    def upsert_perfume(self, perfume: Perfume) -> None:
        self.saved.append(perfume)


def test_scrape_pipeline_collects_listing_pagination_and_saves_perfumes() -> None:
    pages = {
        "https://vicioso.example/collections/all": """
            <article><a href=\"/products/amber-night\" data-product-title=\"Amber Night\"></a><span>€59,90</span></article>
            <a href=\"/collections/all?page=2\">Next</a>
        """,
        "https://vicioso.example/collections/all?page=2": """
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
        "https://vicioso.example/products/fresh-dawn": """
            <meta name=\"description\" content=\"Fresh clean profile.\" />
            <div>Top Notes: Lemon</div>
            <div>Heart Notes: Neroli</div>
            <div>Base Notes: Musk</div>
            <div>Duftfamilie: Frisch</div>
            <img src=\"/images/fresh.jpg\" />
        """,
    }
    pipeline = ScrapePipeline(
        http_client=_FakeHttpClient(pages),
        access_guard=_FakeAccessGuard(),
        perfume_repository=_FakePerfumeRepo(),
        base_url="https://vicioso.example",
    )

    result = pipeline.run(seed_listing_urls=("/collections/all",))

    assert result.scraped_count == 2
    assert result.failed_listing_urls == ()
    assert result.failed_product_urls == ()
    assert result.discovered_product_urls == (
        "https://vicioso.example/products/amber-night",
        "https://vicioso.example/products/fresh-dawn",
    )

    saved = pipeline.perfume_repository.saved
    assert tuple(item.perfume_id for item in saved) == ("amber-night", "fresh-dawn")
    assert saved[0].scent_families == ("Floral",)
    assert saved[1].notes_top == ("Lemon",)


def test_scrape_pipeline_tracks_listing_and_product_failures() -> None:
    pages = {
        "https://vicioso.example/collections/all": """
            <article><a href=\"/products/amber-night\">Amber Night</a></article>
            <a href=\"/collections/all?page=2\">Next</a>
        """,
        "https://vicioso.example/collections/all?page=2": "<div>ignored</div>",
    }

    pipeline = ScrapePipeline(
        http_client=_FakeHttpClient(
            pages,
            failing_urls={
                "https://vicioso.example/collections/all?page=2",
                "https://vicioso.example/products/amber-night",
            },
        ),
        access_guard=_FakeAccessGuard(),
        perfume_repository=_FakePerfumeRepo(),
        base_url="https://vicioso.example",
    )

    result = pipeline.run(seed_listing_urls=("/collections/all",))

    assert result.scraped_count == 0
    assert result.failed_listing_urls == ("https://vicioso.example/collections/all?page=2",)
    assert result.failed_product_urls == ("https://vicioso.example/products/amber-night",)


def test_scrape_pipeline_respects_access_guard_forbidden_url() -> None:
    pages = {
        "https://vicioso.example/collections/all": """
            <article><a href=\"/products/amber-night\">Amber Night</a></article>
        """,
        "https://vicioso.example/products/amber-night": "<div>Top Notes: Bergamot</div>",
    }

    guard = _FakeAccessGuard(blocked_urls={"https://vicioso.example/products/amber-night"})
    pipeline = ScrapePipeline(
        http_client=_FakeHttpClient(pages),
        access_guard=guard,
        perfume_repository=_FakePerfumeRepo(),
        base_url="https://vicioso.example",
    )

    result = pipeline.run(seed_listing_urls=("/collections/all",))

    assert result.scraped_count == 0
    assert result.failed_product_urls == ("https://vicioso.example/products/amber-night",)
    assert pipeline.perfume_repository.saved == []
