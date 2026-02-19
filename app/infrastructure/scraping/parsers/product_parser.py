from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from urllib.parse import urljoin

from app.infrastructure.scraping.normalizers.notes_normalizer import (
    normalize_note_sections,
)
from app.infrastructure.scraping.normalizers.tags_normalizer import (
    normalize_tag_sections,
)

_IMAGE_ATTR_PATTERN = re.compile(
    r"<(?:img|source)[^>]*(?:src|data-src)=[\"'](?P<url>[^\"']+)[\"'][^>]*>",
    re.IGNORECASE,
)
_OG_IMAGE_PATTERN = re.compile(
    r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"'](?P<url>[^\"']+)[\"'][^>]*>",
    re.IGNORECASE,
)
_META_DESC_PATTERN = re.compile(
    r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"'](?P<value>[^\"']+)[\"'][^>]*>",
    re.IGNORECASE,
)
_TYPED_ATTR_VALUE_PATTERN = re.compile(
    r"data-(family|gender|molecule)=[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)
_JSONLD_PATTERN = re.compile(
    r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(?P<body>.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
_TAG_PATTERN = re.compile(r"<[^>]+>")
_SPACE_PATTERN = re.compile(r"\s+")
_SPLIT_TEXT_PATTERN = re.compile(r"\n+")
_SCRIPT_STYLE_PATTERN = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL
)

_LABELS = {
    "notes_top": ("top notes", "head notes", "kopfnote", "kopfnoten"),
    "notes_middle": ("middle notes", "heart notes", "herznote", "herznoten"),
    "notes_base": ("base notes", "basisnote", "basisnoten"),
}


@dataclass(frozen=True)
class ProductPageData:
    description: str
    notes_top: tuple[str, ...]
    notes_middle: tuple[str, ...]
    notes_base: tuple[str, ...]
    gender_tags: tuple[str, ...]
    scent_families: tuple[str, ...]
    molecule_tags: tuple[str, ...]
    image_urls: tuple[str, ...]


def parse_product_page(product_html: str, base_url: str) -> ProductPageData:
    lines = _extract_text_lines(product_html)
    raw_notes = _extract_raw_notes(lines)
    raw_tags = _extract_raw_tags(lines, product_html)

    note_sections = normalize_note_sections(
        raw_notes["notes_top"], raw_notes["notes_middle"], raw_notes["notes_base"]
    )
    tag_sections = normalize_tag_sections(
        raw_tags["gender_tags"], raw_tags["scent_families"], raw_tags["molecule_tags"]
    )

    description = _extract_description(product_html, lines)
    image_urls = _extract_image_urls(product_html, base_url)

    return ProductPageData(
        description=description,
        notes_top=note_sections["notes_top"],
        notes_middle=note_sections["notes_middle"],
        notes_base=note_sections["notes_base"],
        gender_tags=tag_sections["gender_tags"],
        scent_families=tag_sections["scent_families"],
        molecule_tags=tag_sections["molecule_tags"],
        image_urls=image_urls,
    )


def _extract_text_lines(html_text: str) -> tuple[str, ...]:
    without_scripts = _SCRIPT_STYLE_PATTERN.sub(" ", html_text)
    normalized = re.sub(
        r"</?(p|li|div|h\d|section|article|ul|ol|br)\b[^>]*>",
        "\n",
        without_scripts,
        flags=re.IGNORECASE,
    )
    stripped = _TAG_PATTERN.sub(" ", normalized)
    unescaped = html.unescape(stripped)

    raw_lines = _SPLIT_TEXT_PATTERN.split(unescaped)
    lines = [
        _SPACE_PATTERN.sub(" ", line).strip()
        for line in raw_lines
        if _SPACE_PATTERN.sub(" ", line).strip()
    ]
    return tuple(lines)


def _extract_raw_notes(lines: tuple[str, ...]) -> dict[str, list[str]]:
    notes = {"notes_top": [], "notes_middle": [], "notes_base": []}

    for key, labels in _LABELS.items():
        for index, line in enumerate(lines):
            lowered = line.casefold()
            if not any(label in lowered for label in labels):
                continue

            inline = _value_after_colon(line)
            if inline:
                notes[key].append(inline)
            notes[key].extend(_collect_following_lines(lines, index))

    return notes


def _extract_raw_tags(lines: tuple[str, ...], html_text: str) -> dict[str, list[str]]:
    tags = {"gender_tags": [], "scent_families": [], "molecule_tags": []}

    for line in lines:
        lowered = line.casefold()
        if "duftfamilie" in lowered or "family" in lowered or "familie" in lowered:
            tags["scent_families"].append(line)
        if "geschlecht" in lowered or "gender" in lowered:
            tags["gender_tags"].append(line)
        if "molekül" in lowered or "molecule" in lowered:
            tags["molecule_tags"].append(line)

    for attr_kind, attr_value in _TYPED_ATTR_VALUE_PATTERN.findall(html_text):
        lowered = attr_kind.casefold()
        if lowered == "family":
            tags["scent_families"].append(attr_value)
        elif lowered == "gender":
            tags["gender_tags"].append(attr_value)
        elif lowered == "molecule":
            tags["molecule_tags"].append(attr_value)

    return tags


def _extract_description(html_text: str, lines: tuple[str, ...]) -> str:
    meta = _META_DESC_PATTERN.search(html_text)
    if meta:
        return html.unescape(meta.group("value")).strip()

    for entry in _extract_json_ld_product_entries(html_text):
        description = entry.get("description")
        if isinstance(description, str) and description.strip():
            return description.strip()

    candidates = [line for line in lines if len(line) > 30 and ":" not in line]
    return candidates[0] if candidates else ""


def _extract_image_urls(html_text: str, base_url: str) -> tuple[str, ...]:
    urls: list[str] = []

    urls.extend(match.group("url") for match in _IMAGE_ATTR_PATTERN.finditer(html_text))
    urls.extend(match.group("url") for match in _OG_IMAGE_PATTERN.finditer(html_text))

    for entry in _extract_json_ld_product_entries(html_text):
        image_value = entry.get("image")
        if isinstance(image_value, str):
            urls.append(image_value)
        elif isinstance(image_value, list):
            urls.extend(str(item) for item in image_value)

    resolved: list[str] = []
    seen: set[str] = set()
    for url in urls:
        absolute = urljoin(base_url, url.strip())
        if absolute and absolute not in seen:
            seen.add(absolute)
            resolved.append(absolute)

    return tuple(resolved)


def _collect_following_lines(lines: tuple[str, ...], index: int) -> list[str]:
    collected: list[str] = []

    for next_line in lines[index + 1 : index + 4]:
        lowered = next_line.casefold()
        if any(label in lowered for labels in _LABELS.values() for label in labels):
            break
        if any(
            marker in lowered
            for marker in ("duftfamilie", "geschlecht", "molekül", "molecule", "family")
        ):
            break
        if _looks_like_note_line(next_line):
            collected.append(next_line)

    return collected


def _value_after_colon(value: str) -> str:
    if ":" not in value:
        return ""
    return value.split(":", maxsplit=1)[1].strip()


def _looks_like_note_line(value: str) -> bool:
    if len(value) > 35 or "." in value:
        return False
    words = [token for token in value.split(" ") if token]
    return 0 < len(words) <= 4


def _extract_json_ld_product_entries(html_text: str) -> tuple[dict[str, object], ...]:
    entries: list[dict[str, object]] = []

    for match in _JSONLD_PATTERN.finditer(html_text):
        body = html.unescape(match.group("body")).strip()
        parsed = _safe_json_loads(body)
        entries.extend(_flatten_json_ld(parsed))

    return tuple(entry for entry in entries if _is_product_entry(entry))


def _safe_json_loads(value: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def _flatten_json_ld(value: object) -> list[dict[str, object]]:
    if isinstance(value, dict):
        graph = value.get("@graph")
        if isinstance(graph, list):
            return [item for item in graph if isinstance(item, dict)]
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _is_product_entry(entry: dict[str, object]) -> bool:
    entry_type = entry.get("@type")
    if isinstance(entry_type, str):
        return "product" in entry_type.casefold()
    if isinstance(entry_type, list):
        return any(
            isinstance(item, str) and "product" in item.casefold()
            for item in entry_type
        )
    return False
