import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.infrastructure.scraping.parsers.listing_parser import (
    ListingProduct,
    parse_listing_products,
    parse_pagination_urls,
)


def test_parse_listing_products_extracts_name_url_and_price_range() -> None:
    html = """
    <section>
      <article class="product-card">
        <a href="/products/amber-night" data-product-title="Amber Night"></a>
        <span class="price">€59,90 - €89,90</span>
      </article>
      <article class="product-card">
        <a href="/products/fresh-dawn"><span>Fresh Dawn</span></a>
        <span class="price">49.00 EUR</span>
      </article>
    </section>
    """

    products = parse_listing_products(html, "https://vicioso.example")

    assert products == (
        ListingProduct(
            name="Amber Night",
            url="https://vicioso.example/products/amber-night",
            price_min=59.9,
            price_max=89.9,
        ),
        ListingProduct(
            name="Fresh Dawn",
            url="https://vicioso.example/products/fresh-dawn",
            price_min=49.0,
            price_max=49.0,
        ),
    )


def test_parse_listing_products_skips_non_product_and_dedupes_url() -> None:
    html = """
    <div>
      <a href="/collections/all?page=2">Next</a>
      <a href="/products/amber-night" aria-label="Amber Night"></a>
      <a href="https://vicioso.example/products/amber-night">Amber Night Duplicate</a>
    </div>
    """

    products = parse_listing_products(html, "https://vicioso.example")

    assert products == (
        ListingProduct(
            name="Amber Night",
            url="https://vicioso.example/products/amber-night",
            price_min=None,
            price_max=None,
        ),
    )


def test_parse_pagination_urls_extracts_relative_and_absolute_pages() -> None:
    html = """
    <nav>
      <a href="/collections/all?page=2">2</a>
      <a href="https://vicioso.example/collections/all?page=3">3</a>
      <a href="/collections/all/page/4">4</a>
      <a href="/products/amber-night">Product</a>
    </nav>
    """

    pages = parse_pagination_urls(html, "https://vicioso.example")

    assert pages == (
        "https://vicioso.example/collections/all?page=2",
        "https://vicioso.example/collections/all?page=3",
        "https://vicioso.example/collections/all/page/4",
    )


def test_parse_listing_products_uses_title_attribute_fallback() -> None:
    html = """
    <section>
      <article>
        <a href="/products/wood-night" title="Wood Night"></a>
      </article>
    </section>
    """

    products = parse_listing_products(html, "https://vicioso.example")

    assert products == (
        ListingProduct(
            name="Wood Night",
            url="https://vicioso.example/products/wood-night",
            price_min=None,
            price_max=None,
        ),
    )


def test_parse_listing_products_skips_product_without_any_name_signal() -> None:
    html = """
    <section>
      <article>
        <a href="/products/no-name"><span>   </span></a>
      </article>
    </section>
    """

    products = parse_listing_products(html, "https://vicioso.example")

    assert products == ()
