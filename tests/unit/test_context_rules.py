import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.domain.models.perfume import Perfume
from app.domain.models.user_profile import UserProfile
from app.infrastructure.recommendation.features.context_rules import score_context_rules


def test_context_rules_office_energetic_subtle_candidate_scores_high() -> None:
    candidate = Perfume(
        perfume_id="day-spark",
        name="Day Spark",
        url="https://example.com/products/day-spark",
        scent_families=("Fresh", "Citrus", "Clean"),
        notes_top=("Bergamot", "Lemon"),
    )
    profile = UserProfile(
        occasion="office", moods=("energetic",), strength_preference="subtle"
    )

    result = score_context_rules(candidate, profile)

    assert result.occasion_score == 1.0
    assert result.mood_score == 1.0
    assert result.strength_score == 1.0
    assert result.score == 1.0
    assert result.inferred_strength == "subtle"
    assert result.matched_families == ("Citrus", "Clean", "Fresh")


def test_context_rules_evening_cosy_strong_candidate_scores_high() -> None:
    candidate = Perfume(
        perfume_id="night-amber",
        name="Night Amber",
        url="https://example.com/products/night-amber",
        scent_families=("Warm", "Gourmand", "Woody"),
        notes_base=("Amber", "Vanilla"),
    )
    profile = UserProfile(
        occasion="evening", moods=("cosy",), strength_preference="strong"
    )

    result = score_context_rules(candidate, profile)

    assert result.occasion_score == 1.0
    assert result.mood_score == 1.0
    assert result.strength_score == 1.0
    assert result.score == 1.0
    assert result.inferred_strength == "strong"
    assert result.matched_notes == ("Amber", "Vanilla")


def test_context_rules_mismatch_scores_zero() -> None:
    candidate = Perfume(
        perfume_id="night-amber",
        name="Night Amber",
        url="https://example.com/products/night-amber",
        scent_families=("Warm", "Sweet"),
        notes_base=("Amber",),
    )
    profile = UserProfile(
        occasion="office", moods=("calm",), strength_preference="subtle"
    )

    result = score_context_rules(candidate, profile)

    assert result.occasion_score == 0.0
    assert result.mood_score == 0.0
    assert result.strength_score == 0.0
    assert result.score == 0.0


def test_context_rules_returns_zero_when_no_context_preferences() -> None:
    candidate = Perfume(
        perfume_id="balanced",
        name="Balanced",
        url="https://example.com/products/balanced",
        scent_families=("Fresh", "Woody"),
        notes_base=("Musk",),
    )

    result = score_context_rules(candidate, UserProfile())

    assert result.score == 0.0
    assert result.occasion_score == 0.0
    assert result.mood_score == 0.0
    assert result.strength_score == 0.0
    assert result.inferred_strength == "subtle"


def test_context_rules_strength_only_uses_strength_component_weighting() -> None:
    candidate = Perfume(
        perfume_id="balanced",
        name="Balanced",
        url="https://example.com/products/balanced",
        scent_families=("Fresh", "Woody"),
        notes_base=("Musk",),
    )

    medium_profile = UserProfile(strength_preference="medium")
    strong_profile = UserProfile(strength_preference="strong")

    medium_result = score_context_rules(candidate, medium_profile)
    strong_result = score_context_rules(candidate, strong_profile)

    assert medium_result.score == 0.5
    assert medium_result.strength_score == 0.5
    assert strong_result.score == 0.0
    assert strong_result.strength_score == 0.0
