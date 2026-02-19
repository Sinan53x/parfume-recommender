from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

NotePosition = Literal["top", "middle", "base"]


@dataclass(frozen=True)
class NoteEntry:
    note: str
    position: NotePosition


@dataclass(frozen=True)
class Perfume:
    perfume_id: str
    name: str
    url: str
    price_min: float | None = None
    price_max: float | None = None
    gender_tags: tuple[str, ...] = field(default_factory=tuple)
    scent_families: tuple[str, ...] = field(default_factory=tuple)
    molecule_tags: tuple[str, ...] = field(default_factory=tuple)
    notes_top: tuple[str, ...] = field(default_factory=tuple)
    notes_middle: tuple[str, ...] = field(default_factory=tuple)
    notes_base: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    image_urls: tuple[str, ...] = field(default_factory=tuple)
    last_scraped_at: datetime | None = None

    def __post_init__(self) -> None:
        _validate_required(self.perfume_id, "perfume_id")
        _validate_required(self.name, "name")
        _validate_required(self.url, "url")
        _validate_price_range(self.price_min, self.price_max)

        object.__setattr__(self, "gender_tags", _normalize_text_items(self.gender_tags))
        object.__setattr__(self, "scent_families", _normalize_text_items(self.scent_families))
        object.__setattr__(self, "molecule_tags", _normalize_text_items(self.molecule_tags))
        object.__setattr__(self, "notes_top", _normalize_text_items(self.notes_top))
        object.__setattr__(self, "notes_middle", _normalize_text_items(self.notes_middle))
        object.__setattr__(self, "notes_base", _normalize_text_items(self.notes_base))
        object.__setattr__(self, "image_urls", _normalize_text_items(self.image_urls))

    @property
    def notes_all(self) -> tuple[NoteEntry, ...]:
        entries: list[NoteEntry] = []
        entries.extend(NoteEntry(note=note, position="top") for note in self.notes_top)
        entries.extend(NoteEntry(note=note, position="middle") for note in self.notes_middle)
        entries.extend(NoteEntry(note=note, position="base") for note in self.notes_base)
        return tuple(entries)


def _validate_required(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _validate_price_range(price_min: float | None, price_max: float | None) -> None:
    if price_min is None or price_max is None:
        return
    if price_min > price_max:
        raise ValueError("price_min must be <= price_max")


def _normalize_text_items(items: tuple[str, ...]) -> tuple[str, ...]:
    cleaned: list[str] = []
    seen: set[str] = set()

    for item in items:
        normalized = item.strip()
        if not normalized:
            continue

        dedupe_key = normalized.casefold()
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        cleaned.append(normalized)

    return tuple(cleaned)
