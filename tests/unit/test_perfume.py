import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.domain.models.perfume import NoteEntry, Perfume
from app.domain.models.user_profile import UserProfile, UserProfileConstraints


def test_perfume_schema_normalizes_and_builds_notes_all() -> None:
    perfume = Perfume(
        perfume_id="amber-night",
        name="Amber Night",
        url="https://example.com/products/amber-night",
        notes_top=(" Bergamot ", "bergamot", ""),
        notes_middle=("Rose",),
        notes_base=("Vanilla", " Musk "),
        scent_families=("Warm", " warm "),
        image_urls=(" https://img/1.jpg ", ""),
        last_scraped_at=datetime(2026, 2, 19),
    )

    assert perfume.notes_top == ("Bergamot",)
    assert perfume.scent_families == ("Warm",)
    assert perfume.image_urls == ("https://img/1.jpg",)
    assert perfume.notes_all == (
        NoteEntry(note="Bergamot", position="top"),
        NoteEntry(note="Rose", position="middle"),
        NoteEntry(note="Vanilla", position="base"),
        NoteEntry(note="Musk", position="base"),
    )


def test_perfume_requires_identity_fields() -> None:
    with pytest.raises(ValueError, match="perfume_id"):
        Perfume(perfume_id="", name="A", url="https://example.com")

    with pytest.raises(ValueError, match="name"):
        Perfume(perfume_id="id", name=" ", url="https://example.com")

    with pytest.raises(ValueError, match="url"):
        Perfume(perfume_id="id", name="A", url="")


def test_perfume_validates_price_range() -> None:
    with pytest.raises(ValueError, match="price_min"):
        Perfume(
            perfume_id="id",
            name="A",
            url="https://example.com",
            price_min=120.0,
            price_max=80.0,
        )


def test_user_profile_normalizes_fields_and_constraints() -> None:
    profile = UserProfile(
        owned_perfume_ids=(" amber-night ", "Amber-Night", ""),
        liked_notes=(" Vanilla ", "vanilla", "Jasmine"),
        disliked_notes=(" Oud ", "", "oud"),
        preferred_families=(" Warm ", "warm", "Fresh"),
        occasion=" evening ",
        moods=(" Cozy ", "cozy", "Energetic"),
        strength_preference="medium",
        constraints=UserProfileConstraints(
            exclude_notes=(" Patchouli ", "patchouli", ""),
            exclude_families=(" Woody ", "woody"),
        ),
    )

    assert profile.owned_perfume_ids == ("amber-night",)
    assert profile.liked_notes == ("Vanilla", "Jasmine")
    assert profile.disliked_notes == ("Oud",)
    assert profile.preferred_families == ("Warm", "Fresh")
    assert profile.occasion == "evening"
    assert profile.moods == ("Cozy", "Energetic")
    assert profile.constraints.exclude_notes == ("Patchouli",)
    assert profile.constraints.exclude_families == ("Woody",)


def test_user_profile_rejects_invalid_strength() -> None:
    with pytest.raises(ValueError, match="strength_preference"):
        UserProfile(strength_preference="loud")


def test_user_profile_rejects_overlapping_liked_and_disliked_notes() -> None:
    with pytest.raises(ValueError, match="must not overlap"):
        UserProfile(liked_notes=("Vanilla",), disliked_notes=(" vanilla ",))
