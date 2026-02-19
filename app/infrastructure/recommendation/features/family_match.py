from __future__ import annotations

from dataclasses import dataclass

from app.domain.models.perfume import Perfume
from app.domain.models.user_profile import UserProfile


@dataclass(frozen=True)
class FamilyMatchResult:
    score: float
    coverage: float
    precision: float
    matched_families: tuple[str, ...]



def score_family_match(candidate: Perfume, profile: UserProfile) -> FamilyMatchResult:
    preferred_families = {family.casefold() for family in profile.preferred_families}
    candidate_map = _candidate_family_map(candidate)
    candidate_families = set(candidate_map)

    if not preferred_families or not candidate_families:
        return FamilyMatchResult(score=0.0, coverage=0.0, precision=0.0, matched_families=tuple())

    overlap = preferred_families & candidate_families
    coverage = len(overlap) / len(preferred_families)
    precision = len(overlap) / len(candidate_families)
    score = (0.7 * coverage) + (0.3 * precision)
    matched_families = tuple(candidate_map[family] for family in sorted(overlap))
    return FamilyMatchResult(
        score=round(score, 6),
        coverage=round(coverage, 6),
        precision=round(precision, 6),
        matched_families=matched_families,
    )



def _candidate_family_map(candidate: Perfume) -> dict[str, str]:
    family_map: dict[str, str] = {}
    for family in candidate.scent_families:
        key = family.casefold()
        if key not in family_map:
            family_map[key] = family
    return family_map
