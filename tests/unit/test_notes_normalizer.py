import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.infrastructure.scraping.normalizers.notes_normalizer import (
    normalize_note,
    normalize_note_list,
    normalize_note_sections,
    split_note_tokens,
)


def test_normalize_note_removes_labels_and_noise_punctuation() -> None:
    assert normalize_note("Top Notes:  Bergamot  ") == "Bergamot"
    assert normalize_note("Herznoten - Rose") == "Rose"
    assert normalize_note("  Vanilla; ") == "Vanilla"


def test_split_note_tokens_handles_common_delimiters_and_words() -> None:
    tokens = split_note_tokens("bergamot, rose and musk / amber|cedar")
    assert tokens == ("bergamot", "rose", "musk", "amber", "cedar")


def test_normalize_note_list_dedupes_and_filters_empty_tokens() -> None:
    normalized = normalize_note_list(
        [
            "Top Notes: Bergamot, bergamot, ",
            "Rose and Musk",
            "N/A",
            "  ",
        ]
    )
    assert normalized == ("Bergamot", "Rose", "Musk")


def test_normalize_note_sections_normalizes_each_pyramid_group() -> None:
    sections = normalize_note_sections(
        notes_top=["Top Notes: Lemon, Bergamot"],
        notes_middle=["Rose und Jasmin"],
        notes_base=["Vanilla; Musk"],
    )

    assert sections == {
        "notes_top": ("Lemon", "Bergamot"),
        "notes_middle": ("Rose", "Jasmin"),
        "notes_base": ("Vanilla", "Musk"),
    }


def test_normalize_note_handles_german_section_labels_and_spacing() -> None:
    assert normalize_note("Kopfnoten:   Zitrone") == "Zitrone"
    assert normalize_note("Basisnoten -  Sandelholz") == "Sandelholz"


def test_normalize_note_list_filters_noise_variants_and_preserves_order() -> None:
    normalized = normalize_note_list(
        [
            "None",
            "unknown",
            "Cardamom",
            "cardamom",
            "Ambroxan + Musk",
            "Null",
        ]
    )
    assert normalized == ("Cardamom", "Ambroxan", "Musk")
