from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.infrastructure.scraping.normalizers.tags_normalizer import (
    normalize_family_list,
    normalize_tag,
    normalize_tag_list,
    normalize_tag_sections,
)


def test_normalize_tag_removes_labels_and_punctuation() -> None:
    assert normalize_tag("Duftfamilie: Blumig") == "Blumig"
    assert normalize_tag("gender - unisex") == "unisex"
    assert normalize_tag("  Moleküle: Iso E Super; ") == "Iso E Super"


def test_normalize_tag_list_splits_dedupes_and_filters_noise() -> None:
    normalized = normalize_tag_list([
        "fresh, Fresh",
        "warm und woody",
        "N/A",
        "",
    ])
    assert normalized == ("fresh", "warm", "woody")


def test_normalize_family_list_maps_aliases_and_dedupes() -> None:
    normalized = normalize_family_list([
        "Blumig",
        "floral",
        "Süß",
        "gourmandig",
        "Frisch",
    ])
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
