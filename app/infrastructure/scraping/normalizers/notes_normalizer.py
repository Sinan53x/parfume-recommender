from __future__ import annotations

import re
from collections.abc import Iterable

_SECTION_LABEL_PATTERN = re.compile(
    r"^(top notes?|middle notes?|base notes?|head notes?|heart notes?|kopfnote[n]?|herznote[n]?|basisnote[n]?)[:\-\s]+",
    re.IGNORECASE,
)
_SPLIT_PATTERN = re.compile(r"[,;/|+]")
_SPACE_PATTERN = re.compile(r"\s+")
_NOISE_TOKENS = {"", "-", "n/a", "none", "null", "unknown", "k.a."}


def normalize_note(raw_note: str) -> str:
    candidate = _SECTION_LABEL_PATTERN.sub("", raw_note).strip()
    candidate = _SPACE_PATTERN.sub(" ", candidate)
    candidate = candidate.strip(" \t\n\r-_,.;:")
    return candidate


def split_note_tokens(raw_note: str) -> tuple[str, ...]:
    collapsed = _SPACE_PATTERN.sub(" ", raw_note.strip())
    collapsed = re.sub(r"\s+(and|und)\s+", ",", collapsed, flags=re.IGNORECASE)
    tokens = _SPLIT_PATTERN.split(collapsed)
    return tuple(token.strip() for token in tokens if token.strip())


def normalize_note_list(raw_notes: Iterable[str]) -> tuple[str, ...]:
    normalized_notes: list[str] = []
    seen: set[str] = set()

    for raw_note in raw_notes:
        compact_raw_note = _SPACE_PATTERN.sub(" ", raw_note.strip()).casefold()
        if compact_raw_note in _NOISE_TOKENS:
            continue

        for token in split_note_tokens(raw_note):
            normalized = normalize_note(token)
            if normalized.casefold() in _NOISE_TOKENS:
                continue

            dedupe_key = normalized.casefold()
            if not normalized or dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            normalized_notes.append(normalized)

    return tuple(normalized_notes)


def normalize_note_sections(
    notes_top: Iterable[str],
    notes_middle: Iterable[str],
    notes_base: Iterable[str],
) -> dict[str, tuple[str, ...]]:
    return {
        "notes_top": normalize_note_list(notes_top),
        "notes_middle": normalize_note_list(notes_middle),
        "notes_base": normalize_note_list(notes_base),
    }
