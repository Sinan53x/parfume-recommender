from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

StrengthPreference = Literal["subtle", "medium", "strong"]
_ALLOWED_STRENGTHS = {"subtle", "medium", "strong"}


@dataclass(frozen=True)
class UserProfileConstraints:
    exclude_notes: tuple[str, ...] = field(default_factory=tuple)
    exclude_families: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "exclude_notes", _normalize_text_items(self.exclude_notes))
        object.__setattr__(self, "exclude_families", _normalize_text_items(self.exclude_families))


@dataclass(frozen=True)
class UserProfile:
    owned_perfume_ids: tuple[str, ...] = field(default_factory=tuple)
    liked_notes: tuple[str, ...] = field(default_factory=tuple)
    disliked_notes: tuple[str, ...] = field(default_factory=tuple)
    preferred_families: tuple[str, ...] = field(default_factory=tuple)
    occasion: str | None = None
    moods: tuple[str, ...] = field(default_factory=tuple)
    strength_preference: StrengthPreference | None = None
    constraints: UserProfileConstraints = field(default_factory=UserProfileConstraints)

    def __post_init__(self) -> None:
        object.__setattr__(self, "owned_perfume_ids", _normalize_text_items(self.owned_perfume_ids))
        object.__setattr__(self, "liked_notes", _normalize_text_items(self.liked_notes))
        object.__setattr__(self, "disliked_notes", _normalize_text_items(self.disliked_notes))
        object.__setattr__(self, "preferred_families", _normalize_text_items(self.preferred_families))
        object.__setattr__(self, "moods", _normalize_text_items(self.moods))
        object.__setattr__(self, "occasion", _normalize_optional_text(self.occasion))
        _validate_strength(self.strength_preference)
        _validate_note_preferences(self.liked_notes, self.disliked_notes)



def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None



def _validate_strength(strength: str | None) -> None:
    if strength is None:
        return

    if strength not in _ALLOWED_STRENGTHS:
        raise ValueError("strength_preference must be subtle, medium, or strong")



def _validate_note_preferences(
    liked_notes: tuple[str, ...],
    disliked_notes: tuple[str, ...],
) -> None:
    liked = {note.casefold() for note in liked_notes}
    disliked = {note.casefold() for note in disliked_notes}
    overlap = liked & disliked

    if overlap:
        raise ValueError("liked_notes and disliked_notes must not overlap")



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
