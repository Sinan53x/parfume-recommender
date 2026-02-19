from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.domain.models.perfume import Perfume
from app.domain.models.user_profile import UserProfile
from app.infrastructure.recommendation.features.family_match import score_family_match


def test_family_match_scores_overlap_with_explainable_components() -> None:
    candidate = Perfume(
        perfume_id="amber-night",
        name="Amber Night",
        url="https://example.com/products/amber-night",
        scent_families=("Warm", "Gourmand", "Woody", "Fresh"),
    )
    profile = UserProfile(preferred_families=("warm", "Woody", "Floral"))

    result = score_family_match(candidate, profile)

    assert result.coverage == 0.666667
    assert result.precision == 0.5
    assert result.score == 0.616667
    assert result.matched_families == ("Warm", "Woody")


def test_family_match_is_case_insensitive_and_uses_deduped_candidate_families() -> None:
    candidate = Perfume(
        perfume_id="fresh-day",
        name="Fresh Day",
        url="https://example.com/products/fresh-day",
        scent_families=("Fresh", " fresh ", "Citrus"),
    )
    profile = UserProfile(preferred_families=("FRESH", " citrus "))

    result = score_family_match(candidate, profile)

    assert result.coverage == 1.0
    assert result.precision == 1.0
    assert result.score == 1.0
    assert result.matched_families == ("Citrus", "Fresh")


def test_family_match_returns_zero_when_profile_or_candidate_families_are_empty() -> None:
    candidate_with_families = Perfume(
        perfume_id="woody-evening",
        name="Woody Evening",
        url="https://example.com/products/woody-evening",
        scent_families=("Woody",),
    )
    empty_candidate = Perfume(
        perfume_id="plain",
        name="Plain",
        url="https://example.com/products/plain",
    )

    result_no_preferences = score_family_match(candidate_with_families, UserProfile())
    result_no_families = score_family_match(empty_candidate, UserProfile(preferred_families=("Woody",)))

    assert result_no_preferences.score == 0.0
    assert result_no_preferences.coverage == 0.0
    assert result_no_preferences.precision == 0.0
    assert result_no_preferences.matched_families == tuple()

    assert result_no_families.score == 0.0
    assert result_no_families.coverage == 0.0
    assert result_no_families.precision == 0.0
    assert result_no_families.matched_families == tuple()
