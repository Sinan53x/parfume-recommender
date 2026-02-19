from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from app.config.logging import (
    SCRAPE_PARSE_FAILED,
    SCRAPE_RUN_END,
    SCRAPE_RUN_START,
    SCRAPE_URL_FAILED,
    SCRAPE_URL_FETCHED,
    get_logger,
    log_event,
)
from app.domain.models.perfume import Perfume
from app.infrastructure.scraping.parsers.listing_parser import (
    parse_listing_products,
    parse_pagination_urls,
)
from app.infrastructure.scraping.parsers.product_parser import parse_product_page


@dataclass(frozen=True)
class ScrapePipelineResult:
    discovered_product_urls: tuple[str, ...]
    scraped_count: int
    failed_listing_urls: tuple[str, ...]
    failed_product_urls: tuple[str, ...]


class ScrapePipeline:
    def __init__(
        self,
        http_client,
        access_guard,
        perfume_repository,
        base_url: str,
        max_listing_pages: int = 50,
        logger: logging.Logger | None = None,
    ) -> None:
        self.http_client = http_client
        self.access_guard = access_guard
        self.perfume_repository = perfume_repository
        self.base_url = base_url
        self.max_listing_pages = max_listing_pages
        self.logger = logger or get_logger("app.application.pipelines.scrape_pipeline")

    def run(self, seed_listing_urls: tuple[str, ...]) -> ScrapePipelineResult:
        log_event(
            self.logger,
            SCRAPE_RUN_START,
            seed_listing_count=len(seed_listing_urls),
            base_url=self.base_url,
        )
        discovered, failed_listing = self._collect_listing_products(seed_listing_urls)
        scraped_count, failed_products = self._scrape_products(discovered)
        success_rate = _compute_success_rate(scraped_count, len(discovered))

        log_event(
            self.logger,
            SCRAPE_RUN_END,
            discovered_product_count=len(discovered),
            scraped_count=scraped_count,
            failed_listing_count=len(failed_listing),
            failed_product_count=len(failed_products),
            success_rate=success_rate,
        )

        return ScrapePipelineResult(
            discovered_product_urls=tuple(discovered.keys()),
            scraped_count=scraped_count,
            failed_listing_urls=tuple(failed_listing),
            failed_product_urls=tuple(failed_products),
        )

    def _collect_listing_products(
        self, seed_listing_urls: tuple[str, ...]
    ) -> tuple[dict[str, object], list[str]]:
        queue = [urljoin(self.base_url, url) for url in seed_listing_urls]
        visited: set[str] = set()
        products: dict[str, object] = {}
        failed: list[str] = []

        while queue and len(visited) < self.max_listing_pages:
            listing_url = queue.pop(0)
            if listing_url in visited:
                continue
            visited.add(listing_url)

            try:
                listing_html = self._fetch_html(listing_url)
                listing_products = parse_listing_products(listing_html, self.base_url)
                pagination_urls = parse_pagination_urls(listing_html, self.base_url)
            except Exception as exc:
                failed.append(listing_url)
                log_event(
                    self.logger,
                    SCRAPE_PARSE_FAILED,
                    level=logging.WARNING,
                    stage="listing",
                    url=listing_url,
                    error_type=type(exc).__name__,
                )
                continue

            for product in listing_products:
                products.setdefault(product.url, product)

            for page_url in pagination_urls:
                if page_url not in visited:
                    queue.append(page_url)

        return products, failed

    def _scrape_products(
        self, discovered_products: dict[str, object]
    ) -> tuple[int, list[str]]:
        failed: list[str] = []
        scraped_count = 0

        for product_url, product_summary in discovered_products.items():
            try:
                product_html = self._fetch_html(product_url)
                product_data = parse_product_page(product_html, self.base_url)
                perfume = _build_perfume(product_summary, product_data)
                self.perfume_repository.upsert_perfume(perfume)
                scraped_count += 1
            except Exception as exc:
                failed.append(product_url)
                log_event(
                    self.logger,
                    SCRAPE_PARSE_FAILED,
                    level=logging.WARNING,
                    stage="product",
                    url=product_url,
                    error_type=type(exc).__name__,
                )

        return scraped_count, failed

    def _fetch_html(self, url: str) -> str:
        try:
            self.access_guard.enforce(url)
            response = self.http_client.fetch(url)
        except Exception as exc:
            log_event(
                self.logger,
                SCRAPE_URL_FAILED,
                level=logging.WARNING,
                url=url,
                error_type=type(exc).__name__,
            )
            raise

        log_event(
            self.logger,
            SCRAPE_URL_FETCHED,
            url=url,
            status_code=response.status_code,
            content_length=len(response.text),
        )
        return response.text


def _build_perfume(product_summary, product_data) -> Perfume:
    perfume_url = product_summary.url

    return Perfume(
        perfume_id=_perfume_id_from_url(perfume_url),
        name=product_summary.name,
        url=perfume_url,
        price_min=product_summary.price_min,
        price_max=product_summary.price_max,
        gender_tags=product_data.gender_tags,
        scent_families=product_data.scent_families,
        molecule_tags=product_data.molecule_tags,
        notes_top=product_data.notes_top,
        notes_middle=product_data.notes_middle,
        notes_base=product_data.notes_base,
        description=product_data.description,
        image_urls=product_data.image_urls,
        last_scraped_at=datetime.now(tz=timezone.utc),
    )


def _perfume_id_from_url(url: str) -> str:
    parts = [part for part in urlparse(url).path.split("/") if part]
    if "products" in parts:
        index = parts.index("products")
        if index + 1 < len(parts):
            return parts[index + 1]

    if parts:
        return parts[-1]

    raise ValueError(f"Cannot derive perfume_id from url: {url}")


def _compute_success_rate(scraped_count: int, discovered_count: int) -> float:
    if discovered_count == 0:
        return 0.0
    return round(scraped_count / discovered_count, 4)
