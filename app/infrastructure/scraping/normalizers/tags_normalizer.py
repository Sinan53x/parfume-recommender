from __future__ import annotations

import re
from collections.abc import Iterable

_SPACE_PATTERN = re.compile(r"\s+")
_SPLIT_PATTERN = re.compile(r"[,;/|+]")
_LABEL_PATTERN = re.compile(
    r"^(duftfamilie|familie|family|geschlecht|gender|molek[üu]le|molecules?)[:\-\s]+",
    re.IGNORECASE,
)
_NOISE_TOKENS = {"", "-", "n/a", "none", "null", "unknown", "k.a."}
_FAMILY_ALIASES = {
    "blumig": "Floral",
    "floral": "Floral",
    "frisch": "Fresh",
    "fresh": "Fresh",
    "gourmandig": "Gourmand",
    "gourmand": "Gourmand",
    "holzig": "Woody",
    "woody": "Woody",
    "orientalisch": "Oriental",
    "oriental": "Oriental",
    "suess": "Sweet",
    "suss": "Sweet",
    "süß": "Sweet",
    "süss": "Sweet",
    "sweet": "Sweet",
    "warm": "Warm",
}


def normalize_tag(raw_tag: str) -> str:
    candidate = _LABEL_PATTERN.sub("", raw_tag.strip())
    candidate = _SPACE_PATTERN.sub(" ", candidate)
    candidate = candidate.strip(" \t\n\r-_,.;:")
    return candidate


def split_tag_tokens(raw_tag: str) -> tuple[str, ...]:
    collapsed = _SPACE_PATTERN.sub(" ", raw_tag.strip())
    collapsed = re.sub(r"\s+(and|und)\s+", ",", collapsed, flags=re.IGNORECASE)
    tokens = _SPLIT_PATTERN.split(collapsed)
    return tuple(token.strip() for token in tokens if token.strip())


def normalize_tag_list(raw_tags: Iterable[str]) -> tuple[str, ...]:
    normalized_tags: list[str] = []
    seen: set[str] = set()

    for raw_tag in raw_tags:
        compact_raw_tag = _SPACE_PATTERN.sub(" ", raw_tag.strip()).casefold()
        if compact_raw_tag in _NOISE_TOKENS:
            continue

        for token in split_tag_tokens(raw_tag):
            normalized = normalize_tag(token)
            dedupe_key = normalized.casefold()
            if not normalized or dedupe_key in _NOISE_TOKENS or dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            normalized_tags.append(normalized)

    return tuple(normalized_tags)


def normalize_family_list(raw_families: Iterable[str]) -> tuple[str, ...]:
    normalized_families: list[str] = []
    seen: set[str] = set()

    for family in normalize_tag_list(raw_families):
        alias_key = family.casefold()
        canonical = _FAMILY_ALIASES.get(alias_key, family)
        dedupe_key = canonical.casefold()
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        normalized_families.append(canonical)

    return tuple(normalized_families)


def normalize_tag_sections(
    gender_tags: Iterable[str],
    scent_families: Iterable[str],
    molecule_tags: Iterable[str],
) -> dict[str, tuple[str, ...]]:
    return {
        "gender_tags": normalize_tag_list(gender_tags),
        "scent_families": normalize_family_list(scent_families),
        "molecule_tags": normalize_tag_list(molecule_tags),
    }
