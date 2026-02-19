import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.infrastructure.scraping.normalizers.tags_normalizer import (
    normalize_family_list,
    normalize_tag,
    normalize_tag_list,
    normalize_tag_sections,
    split_tag_tokens,
)


def test_normalize_tag_removes_labels_and_punctuation() -> None:
    assert normalize_tag("Duftfamilie: Blumig") == "Blumig"
    assert normalize_tag("gender - unisex") == "unisex"
    assert normalize_tag("  Moleküle: Iso E Super; ") == "Iso E Super"


def test_normalize_tag_list_splits_dedupes_and_filters_noise() -> None:
    normalized = normalize_tag_list(
        [
            "fresh, Fresh",
            "warm und woody",
            "N/A",
            "",
        ]
    )
    assert normalized == ("fresh", "warm", "woody")


def test_normalize_family_list_maps_aliases_and_dedupes() -> None:
    normalized = normalize_family_list(
        [
            "Blumig",
            "floral",
            "Süß",
            "gourmandig",
            "Frisch",
        ]
    )
    assert normalized == ("Floral", "Sweet", "Gourmand", "Fresh")


def test_normalize_tag_sections_applies_correct_normalizers() -> None:
    sections = normalize_tag_sections(
        gender_tags=["Gender: Unisex", "unisex"],
        scent_families=["Blumig", "Frisch"],
        molecule_tags=["Moleküle: Iso E Super", "Ambroxan"],
    )

    assert sections == {
        "gender_tags": ("Unisex",),
        "scent_families": ("Floral", "Fresh"),
        "molecule_tags": ("Iso E Super", "Ambroxan"),
    }


def test_split_tag_tokens_handles_plus_pipe_and_semicolon() -> None:
    tokens = split_tag_tokens("warm + woody|fresh; floral")
    assert tokens == ("warm", "woody", "fresh", "floral")


def test_normalize_family_list_maps_sweet_variants_to_single_canonical_value() -> None:
    normalized = normalize_family_list(["Süß", "süss", "sweet", "suess"])
    assert normalized == ("Sweet",)


def test_normalize_tag_sections_filters_noise_from_each_section() -> None:
    sections = normalize_tag_sections(
        gender_tags=["Gender: Unisex", "n/a", "unknown"],
        scent_families=["Blumig", "none", "Frisch"],
        molecule_tags=["Moleküle: Ambroxan", "null", "k.a."],
    )

    assert sections == {
        "gender_tags": ("Unisex",),
        "scent_families": ("Floral", "Fresh"),
        "molecule_tags": ("Ambroxan",),
    }
