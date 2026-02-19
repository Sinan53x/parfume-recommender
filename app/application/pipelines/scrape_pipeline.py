from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

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
    ) -> None:
        self.http_client = http_client
        self.access_guard = access_guard
        self.perfume_repository = perfume_repository
        self.base_url = base_url
        self.max_listing_pages = max_listing_pages

    def run(self, seed_listing_urls: tuple[str, ...]) -> ScrapePipelineResult:
        discovered, failed_listing = self._collect_listing_products(seed_listing_urls)
        scraped_count, failed_products = self._scrape_products(discovered)

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
            except Exception:
                failed.append(listing_url)
                continue

            for product in parse_listing_products(listing_html, self.base_url):
                products.setdefault(product.url, product)

            for page_url in parse_pagination_urls(listing_html, self.base_url):
                if page_url not in visited:
                    queue.append(page_url)

        return products, failed

    def _scrape_products(self, discovered_products: dict[str, object]) -> tuple[int, list[str]]:
        failed: list[str] = []
        scraped_count = 0

        for product_url, product_summary in discovered_products.items():
            try:
                product_html = self._fetch_html(product_url)
                product_data = parse_product_page(product_html, self.base_url)
                perfume = _build_perfume(product_summary, product_data)
                self.perfume_repository.upsert_perfume(perfume)
                scraped_count += 1
            except Exception:
                failed.append(product_url)

        return scraped_count, failed

    def _fetch_html(self, url: str) -> str:
        self.access_guard.enforce(url)
        response = self.http_client.fetch(url)
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
