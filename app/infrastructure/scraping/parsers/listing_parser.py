from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

_ANCHOR_PATTERN = re.compile(
    r"<a(?P<attrs>[^>]*?)href=[\"'](?P<href>[^\"']+)[\"'](?P<tail>[^>]*)>(?P<body>.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
_ATTR_PATTERN = re.compile(
    r"(?P<name>[\w:-]+)=[\"'](?P<value>[^\"']*)[\"']", re.IGNORECASE
)
_TAG_PATTERN = re.compile(r"<[^>]+>")
_SPACE_PATTERN = re.compile(r"\s+")
_PRODUCT_PATH_PATTERN = re.compile(r"/products/[^/?#\"']+", re.IGNORECASE)
_PAGE_PATTERN = re.compile(r"([?&]page=\d+)|(/page/\d+)", re.IGNORECASE)
_PRICE_PATTERN = re.compile(
    r"(?:(?:€|\$|£)\s*\d+(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?\s*(?:€|eur|usd|gbp))",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ListingProduct:
    name: str
    url: str
    price_min: float | None
    price_max: float | None


def parse_listing_products(
    listing_html: str, base_url: str
) -> tuple[ListingProduct, ...]:
    products: list[ListingProduct] = []
    seen_urls: set[str] = set()

    for anchor in _ANCHOR_PATTERN.finditer(listing_html):
        href = anchor.group("href")
        if not _PRODUCT_PATH_PATTERN.search(href):
            continue

        url = urljoin(base_url, href)
        if url in seen_urls:
            continue

        name = _extract_anchor_name(
            anchor.group("attrs"), anchor.group("tail"), anchor.group("body")
        )
        if not name:
            continue

        window = _extract_card_window(listing_html, anchor.start(), anchor.end())
        price_min, price_max = _extract_price_range(window)
        products.append(
            ListingProduct(name=name, url=url, price_min=price_min, price_max=price_max)
        )
        seen_urls.add(url)

    return tuple(products)


def parse_pagination_urls(listing_html: str, base_url: str) -> tuple[str, ...]:
    page_urls: list[str] = []
    seen: set[str] = set()

    for anchor in _ANCHOR_PATTERN.finditer(listing_html):
        href = anchor.group("href")
        if not _PAGE_PATTERN.search(href):
            continue

        absolute_url = urljoin(base_url, href)
        if absolute_url in seen:
            continue

        seen.add(absolute_url)
        page_urls.append(absolute_url)

    return tuple(page_urls)


def _extract_anchor_name(attrs: str, tail: str, body: str) -> str:
    attributes = _extract_attributes(f"{attrs} {tail}")
    for key in ("data-product-title", "aria-label", "title"):
        value = _clean_text(attributes.get(key, ""))
        if value:
            return value
    return _clean_text(body)


def _extract_attributes(raw_attrs: str) -> dict[str, str]:
    return {
        match.group("name").lower(): match.group("value")
        for match in _ATTR_PATTERN.finditer(raw_attrs)
    }


def _clean_text(value: str) -> str:
    no_tags = _TAG_PATTERN.sub(" ", value)
    normalized = _SPACE_PATTERN.sub(" ", no_tags).strip()
    return normalized


def _extract_price_range(html_window: str) -> tuple[float | None, float | None]:
    values: list[float] = []

    for raw_price in _PRICE_PATTERN.findall(html_window):
        amount = _parse_price(raw_price)
        if amount is not None:
            values.append(amount)

    if not values:
        return None, None

    return min(values), max(values)


def _extract_card_window(listing_html: str, anchor_start: int, anchor_end: int) -> str:
    card_start = listing_html.rfind("<article", 0, anchor_start)
    card_end = listing_html.find("</article>", anchor_end)

    if card_start != -1 and card_end != -1:
        return listing_html[card_start : card_end + len("</article>")]

    fallback_start = max(anchor_start - 220, 0)
    fallback_end = min(anchor_end + 220, len(listing_html))
    return listing_html[fallback_start:fallback_end]


def _parse_price(raw_price: str) -> float | None:
    numeric = re.sub(r"[^0-9.,]", "", raw_price)
    if not numeric:
        return None

    if "," in numeric and "." in numeric:
        numeric = numeric.replace(".", "").replace(",", ".")
    elif "," in numeric:
        numeric = numeric.replace(",", ".")

    try:
        return float(numeric)
    except ValueError:
        return None
