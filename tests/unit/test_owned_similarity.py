import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.domain.models.perfume import Perfume
from app.domain.models.user_profile import UserProfile
from app.infrastructure.recommendation.features.owned_similarity import (
    score_owned_similarity,
)


def test_owned_similarity_uses_best_owned_match_and_returns_overlap_details() -> None:
    candidate = Perfume(
        perfume_id="amber-night",
        name="Amber Night",
        url="https://example.com/products/amber-night",
        scent_families=("Warm", "Woody"),
        notes_middle=("Rose",),
        notes_base=("Vanilla", "Musk"),
    )
    owned_close = Perfume(
        perfume_id="gold-amber",
        name="Gold Amber",
        url="https://example.com/products/gold-amber",
        scent_families=("Warm", "Spicy"),
        notes_middle=("Rose",),
        notes_base=("Vanilla", "Patchouli"),
    )
    owned_far = Perfume(
        perfume_id="ocean-air",
        name="Ocean Air",
        url="https://example.com/products/ocean-air",
        scent_families=("Fresh",),
        notes_top=("Lemon",),
    )

    result = score_owned_similarity(candidate, (owned_far, owned_close), UserProfile())

    assert result.score == 0.45
    assert result.matched_owned_perfume_id == "gold-amber"
    assert result.matched_notes == ("Rose", "Vanilla")
    assert result.matched_families == ("Warm",)
    assert result.owned_penalty == 0.0
    assert result.is_owned is False


def test_owned_similarity_applies_penalty_when_candidate_is_already_owned() -> None:
    candidate = Perfume(
        perfume_id="amber-night",
        name="Amber Night",
        url="https://example.com/products/amber-night",
        scent_families=("Warm",),
        notes_base=("Vanilla",),
    )
    owned = Perfume(
        perfume_id="gold-amber",
        name="Gold Amber",
        url="https://example.com/products/gold-amber",
        scent_families=("Warm",),
        notes_base=("Vanilla",),
    )
    profile = UserProfile(owned_perfume_ids=(" amber-night ",))

    result = score_owned_similarity(
        candidate, (owned,), profile, owned_penalty_value=0.35
    )

    assert result.score == 1.0
    assert result.owned_penalty == 0.35
    assert result.is_owned is True


def test_owned_similarity_returns_zero_without_owned_candidates() -> None:
    candidate = Perfume(
        perfume_id="amber-night",
        name="Amber Night",
        url="https://example.com/products/amber-night",
        notes_base=("Vanilla",),
    )

    result = score_owned_similarity(candidate, tuple(), UserProfile())

    assert result.score == 0.0
    assert result.matched_owned_perfume_id is None
    assert result.matched_notes == tuple()
    assert result.matched_families == tuple()
    assert result.owned_penalty == 0.0
    assert result.is_owned is False


def test_owned_similarity_is_case_insensitive_for_notes_and_families() -> None:
    candidate = Perfume(
        perfume_id="spice-route",
        name="Spice Route",
        url="https://example.com/products/spice-route",
        scent_families=("Warm", "Woody"),
        notes_top=("Saffron",),
        notes_base=("Amber",),
    )
    owned = Perfume(
        perfume_id="night-spice",
        name="Night Spice",
        url="https://example.com/products/night-spice",
        scent_families=("warm", "Resinous"),
        notes_top=("saffron",),
        notes_base=("amber",),
    )

    result = score_owned_similarity(candidate, (owned,), UserProfile())

    assert result.score == 0.8
    assert result.matched_notes == ("Amber", "Saffron")
    assert result.matched_families == ("Warm",)
