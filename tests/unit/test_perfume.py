from datetime import datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.domain.models.perfume import NoteEntry, Perfume


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
