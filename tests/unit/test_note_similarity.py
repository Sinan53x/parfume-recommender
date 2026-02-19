from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.domain.models.perfume import Perfume
from app.domain.models.user_profile import UserProfile
from app.infrastructure.recommendation.features.note_similarity import score_note_similarity


def test_note_similarity_scores_overlap_with_explainable_components() -> None:
    candidate = Perfume(
        perfume_id="amber-night",
        name="Amber Night",
        url="https://example.com/products/amber-night",
        notes_top=("Bergamot",),
        notes_middle=("Rose", "Jasmine"),
        notes_base=("Vanilla", "Musk"),
    )
    profile = UserProfile(liked_notes=("Vanilla", "Jasmine", "Saffron"))

    result = score_note_similarity(candidate, profile)

    assert result.coverage == 0.666667
    assert result.precision == 0.4
    assert result.score == 0.586667
    assert result.matched_notes == ("Jasmine", "Vanilla")


def test_note_similarity_is_case_insensitive_and_uses_deduped_candidate_notes() -> None:
    candidate = Perfume(
        perfume_id="fresh-day",
        name="Fresh Day",
        url="https://example.com/products/fresh-day",
        notes_top=("Lemon", "lemon"),
        notes_middle=("Neroli",),
        notes_base=("Musk",),
    )
    profile = UserProfile(liked_notes=(" lemon ", "NEROLI"))

    result = score_note_similarity(candidate, profile)

    assert result.coverage == 1.0
    assert result.precision == 0.666667
    assert result.score == 0.9
    assert result.matched_notes == ("Lemon", "Neroli")


def test_note_similarity_returns_zero_when_profile_or_candidate_notes_are_empty() -> None:
    candidate_with_notes = Perfume(
        perfume_id="woody-evening",
        name="Woody Evening",
        url="https://example.com/products/woody-evening",
        notes_base=("Cedar",),
    )
    empty_candidate = Perfume(
        perfume_id="plain",
        name="Plain",
        url="https://example.com/products/plain",
    )

    result_no_preferences = score_note_similarity(candidate_with_notes, UserProfile())
    result_no_notes = score_note_similarity(empty_candidate, UserProfile(liked_notes=("Cedar",)))

    assert result_no_preferences.score == 0.0
    assert result_no_preferences.coverage == 0.0
    assert result_no_preferences.precision == 0.0
    assert result_no_preferences.matched_notes == tuple()

    assert result_no_notes.score == 0.0
    assert result_no_notes.coverage == 0.0
    assert result_no_notes.precision == 0.0
    assert result_no_notes.matched_notes == tuple()
