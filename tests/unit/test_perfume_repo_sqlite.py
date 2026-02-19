from datetime import datetime
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.domain.models.perfume import Perfume
from app.infrastructure.persistence.sqlite.perfume_repo_sqlite import PerfumeRepositorySqlite


def _sample_perfume(perfume_id: str = "amber-night") -> Perfume:
    return Perfume(
        perfume_id=perfume_id,
        name="Amber Night",
        url=f"https://vicioso.example/products/{perfume_id}",
        price_min=59.9,
        price_max=89.9,
        gender_tags=("Unisex",),
        scent_families=("Floral", "Warm"),
        molecule_tags=("Iso E Super",),
        notes_top=("Bergamot",),
        notes_middle=("Rose",),
        notes_base=("Vanilla", "Musk"),
        description="Warm floral with depth.",
        image_urls=("https://img.example/amber.jpg",),
        last_scraped_at=datetime(2026, 2, 19, 12, 30, 0),
    )


def test_initialize_schema_creates_perfumes_table() -> None:
    connection = sqlite3.connect(":memory:")
    repo = PerfumeRepositorySqlite(connection)

    repo.initialize_schema()

    rows = connection.execute("PRAGMA table_info(perfumes)").fetchall()
    columns = {row[1] for row in rows}
    assert {
        "perfume_id",
        "name",
        "url",
        "notes_all",
        "last_scraped_at",
    }.issubset(columns)


def test_upsert_and_get_perfume_round_trip() -> None:
    connection = sqlite3.connect(":memory:")
    repo = PerfumeRepositorySqlite(connection)
    repo.initialize_schema()

    expected = _sample_perfume()
    repo.upsert_perfume(expected)

    loaded = repo.get_perfume("amber-night")

    assert loaded == expected


def test_upsert_overwrites_existing_perfume() -> None:
    connection = sqlite3.connect(":memory:")
    repo = PerfumeRepositorySqlite(connection)
    repo.initialize_schema()

    repo.upsert_perfume(_sample_perfume())
    updated = Perfume(
        perfume_id="amber-night",
        name="Amber Night Intense",
        url="https://vicioso.example/products/amber-night",
        price_min=69.9,
        price_max=99.9,
        notes_top=("Mandarin",),
        notes_middle=("Rose",),
        notes_base=("Amber",),
    )
    repo.upsert_perfume(updated)

    loaded = repo.get_perfume("amber-night")

    assert loaded == updated


def test_list_perfumes_returns_ordered_page() -> None:
    connection = sqlite3.connect(":memory:")
    repo = PerfumeRepositorySqlite(connection)
    repo.initialize_schema()

    repo.upsert_perfumes((_sample_perfume("b"), _sample_perfume("a"), _sample_perfume("c")))

    page = repo.list_perfumes(limit=2, offset=1)

    assert tuple(item.perfume_id for item in page) == ("b", "c")
