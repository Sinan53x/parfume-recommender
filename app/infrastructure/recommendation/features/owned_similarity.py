from __future__ import annotations

from dataclasses import dataclass

from app.domain.models.perfume import Perfume
from app.domain.models.user_profile import UserProfile


@dataclass(frozen=True)
class OwnedSimilarityResult:
    score: float
    matched_owned_perfume_id: str | None
    matched_notes: tuple[str, ...]
    matched_families: tuple[str, ...]
    owned_penalty: float
    is_owned: bool



def score_owned_similarity(
    candidate: Perfume,
    owned_perfumes: tuple[Perfume, ...],
    profile: UserProfile,
    owned_penalty_value: float = 1.0,
) -> OwnedSimilarityResult:
    candidate_notes = _note_map(candidate)
    candidate_families = _family_map(candidate)
    is_owned = candidate.perfume_id.casefold() in {pid.casefold() for pid in profile.owned_perfume_ids}
    best = (0.0, None, tuple(), tuple())

    for owned in owned_perfumes:
        owned_notes = _note_map(owned)
        owned_families = _family_map(owned)
        note_overlap = set(candidate_notes) & set(owned_notes)
        family_overlap = set(candidate_families) & set(owned_families)
        note_score = _jaccard(set(candidate_notes), set(owned_notes))
        family_score = _jaccard(set(candidate_families), set(owned_families))
        similarity = (0.7 * note_score) + (0.3 * family_score)
        matched_notes = tuple(candidate_notes[note] for note in sorted(note_overlap))
        matched_families = tuple(candidate_families[family] for family in sorted(family_overlap))

        if similarity > best[0]:
            best = (similarity, owned.perfume_id, matched_notes, matched_families)

    penalty = owned_penalty_value if is_owned else 0.0
    return OwnedSimilarityResult(
        score=round(best[0], 6),
        matched_owned_perfume_id=best[1],
        matched_notes=best[2],
        matched_families=best[3],
        owned_penalty=round(penalty, 6),
        is_owned=is_owned,
    )



def _note_map(perfume: Perfume) -> dict[str, str]:
    note_map: dict[str, str] = {}
    for note in perfume.notes_top + perfume.notes_middle + perfume.notes_base:
        key = note.casefold()
        if key not in note_map:
            note_map[key] = note
    return note_map



def _family_map(perfume: Perfume) -> dict[str, str]:
    family_map: dict[str, str] = {}
    for family in perfume.scent_families:
        key = family.casefold()
        if key not in family_map:
            family_map[key] = family
    return family_map



def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)
