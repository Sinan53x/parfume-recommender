from __future__ import annotations

from dataclasses import dataclass

from app.domain.models.perfume import Perfume
from app.domain.models.user_profile import UserProfile

_OCCASION_TARGETS: dict[str, set[str]] = {
    "office": {"fresh", "clean", "citrus", "green", "aquatic", "musk"},
    "date": {"warm", "sweet", "woody", "gourmand", "amber", "floral"},
    "evening": {"warm", "sweet", "woody", "gourmand", "amber", "spicy"},
    "everyday": {"fresh", "clean", "citrus", "green", "musk", "woody"},
}
_MOOD_TARGETS: dict[str, set[str]] = {
    "cosy": {"warm", "sweet", "gourmand", "amber", "vanilla", "musk", "woody"},
    "cozy": {"warm", "sweet", "gourmand", "amber", "vanilla", "musk", "woody"},
    "elegant": {"woody", "floral", "powdery", "musk", "amber"},
    "energetic": {"fresh", "citrus", "green", "aquatic", "spicy"},
    "calm": {"clean", "musk", "powdery", "green", "floral"},
}
_STRONG_CUES = {"warm", "sweet", "gourmand", "oriental", "amber", "oud", "spicy", "resinous", "leather", "tobacco"}
_SUBTLE_CUES = {"fresh", "clean", "citrus", "aquatic", "green", "soapy", "powdery", "soft", "musk"}
_STRENGTH_ORDER = ("subtle", "medium", "strong")


@dataclass(frozen=True)
class ContextRulesResult:
    score: float
    occasion_score: float
    mood_score: float
    strength_score: float
    inferred_strength: str
    matched_families: tuple[str, ...]
    matched_notes: tuple[str, ...]



def score_context_rules(candidate: Perfume, profile: UserProfile) -> ContextRulesResult:
    family_map = _family_map(candidate)
    note_map = _note_map(candidate)
    candidate_tokens = set(family_map) | set(note_map)
    inferred_strength = _infer_strength(candidate_tokens)

    occasion_targets = _occasion_targets(profile.occasion)
    mood_targets, mood_available = _mood_targets(profile.moods)
    occasion_score = _match_score(candidate_tokens, occasion_targets) if occasion_targets else 0.0
    mood_score = _match_score(candidate_tokens, mood_targets) if mood_available else 0.0
    strength_score = _strength_score(profile.strength_preference, inferred_strength)
    final_score = _weighted_score(occasion_targets, mood_available, profile.strength_preference, occasion_score, mood_score, strength_score)
    active_targets = occasion_targets | mood_targets

    return ContextRulesResult(
        score=round(final_score, 6),
        occasion_score=round(occasion_score, 6),
        mood_score=round(mood_score, 6),
        strength_score=round(strength_score, 6),
        inferred_strength=inferred_strength,
        matched_families=tuple(family_map[key] for key in sorted(set(family_map) & active_targets)),
        matched_notes=tuple(note_map[key] for key in sorted(set(note_map) & active_targets)),
    )



def _weighted_score(
    occasion_targets: set[str],
    mood_available: bool,
    strength_preference: str | None,
    occasion_score: float,
    mood_score: float,
    strength_score: float,
) -> float:
    components: list[tuple[float, float]] = []
    if occasion_targets:
        components.append((0.4, occasion_score))
    if mood_available:
        components.append((0.35, mood_score))
    if strength_preference is not None:
        components.append((0.25, strength_score))
    if not components:
        return 0.0

    weighted_total = sum(weight * value for weight, value in components)
    total_weight = sum(weight for weight, _ in components)
    return weighted_total / total_weight



def _match_score(candidate_tokens: set[str], targets: set[str]) -> float:
    overlap = len(candidate_tokens & targets)
    if overlap <= 0:
        return 0.0
    if overlap == 1:
        return 0.6
    return 1.0



def _occasion_targets(occasion: str | None) -> set[str]:
    if not occasion:
        return set()
    return _OCCASION_TARGETS.get(occasion.casefold(), set())



def _mood_targets(moods: tuple[str, ...]) -> tuple[set[str], bool]:
    targets: set[str] = set()
    available = False
    for mood in moods:
        mood_targets = _MOOD_TARGETS.get(mood.casefold())
        if mood_targets is None:
            continue
        targets |= mood_targets
        available = True
    return targets, available



def _strength_score(preference: str | None, inferred_strength: str) -> float:
    if preference is None:
        return 0.0

    preference_index = _STRENGTH_ORDER.index(preference)
    inferred_index = _STRENGTH_ORDER.index(inferred_strength)
    distance = abs(preference_index - inferred_index)
    if distance == 0:
        return 1.0
    if distance == 1:
        return 0.5
    return 0.0



def _infer_strength(candidate_tokens: set[str]) -> str:
    strong_hits = len(candidate_tokens & _STRONG_CUES)
    subtle_hits = len(candidate_tokens & _SUBTLE_CUES)
    signal = strong_hits - subtle_hits
    if signal >= 2:
        return "strong"
    if signal <= -2:
        return "subtle"
    return "medium"



def _family_map(perfume: Perfume) -> dict[str, str]:
    family_map: dict[str, str] = {}
    for family in perfume.scent_families:
        key = family.casefold()
        if key not in family_map:
            family_map[key] = family
    return family_map



def _note_map(perfume: Perfume) -> dict[str, str]:
    note_map: dict[str, str] = {}
    for note in perfume.notes_top + perfume.notes_middle + perfume.notes_base:
        key = note.casefold()
        if key not in note_map:
            note_map[key] = note
    return note_map
