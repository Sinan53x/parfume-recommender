from __future__ import annotations

from dataclasses import dataclass

from app.domain.models.perfume import Perfume
from app.domain.models.user_profile import UserProfile


@dataclass(frozen=True)
class NoteSimilarityResult:
    score: float
    coverage: float
    precision: float
    matched_notes: tuple[str, ...]



def score_note_similarity(candidate: Perfume, profile: UserProfile) -> NoteSimilarityResult:
    desired_notes = {note.casefold() for note in profile.liked_notes}
    candidate_map = _candidate_note_map(candidate)
    candidate_notes = set(candidate_map)

    if not desired_notes or not candidate_notes:
        return NoteSimilarityResult(score=0.0, coverage=0.0, precision=0.0, matched_notes=tuple())

    overlap = desired_notes & candidate_notes
    coverage = len(overlap) / len(desired_notes)
    precision = len(overlap) / len(candidate_notes)
    score = (0.7 * coverage) + (0.3 * precision)
    matched_notes = tuple(candidate_map[note] for note in sorted(overlap))
    return NoteSimilarityResult(
        score=round(score, 6),
        coverage=round(coverage, 6),
        precision=round(precision, 6),
        matched_notes=matched_notes,
    )



def _candidate_note_map(candidate: Perfume) -> dict[str, str]:
    note_map: dict[str, str] = {}
    for note in candidate.notes_top + candidate.notes_middle + candidate.notes_base:
        key = note.casefold()
        if key not in note_map:
            note_map[key] = note
    return note_map
