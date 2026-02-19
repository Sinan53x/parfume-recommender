from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import sqlite3

from app.domain.models.perfume import Perfume


class PerfumeRepositorySqlite:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    def initialize_schema(self, schema_path: str | None = None) -> None:
        sql = _load_schema_sql(schema_path)
        self.connection.executescript(sql)
        self.connection.commit()

    def upsert_perfume(self, perfume: Perfume) -> None:
        self.connection.execute(_UPSERT_SQL, _perfume_to_row(perfume))
        self.connection.commit()

    def upsert_perfumes(self, perfumes: tuple[Perfume, ...]) -> None:
        params = [_perfume_to_row(perfume) for perfume in perfumes]
        self.connection.executemany(_UPSERT_SQL, params)
        self.connection.commit()

    def get_perfume(self, perfume_id: str) -> Perfume | None:
        query = "SELECT * FROM perfumes WHERE perfume_id = ?"
        row = self.connection.execute(query, (perfume_id,)).fetchone()
        if row is None:
            return None
        return _row_to_perfume(row)

    def list_perfumes(self, limit: int = 100, offset: int = 0) -> tuple[Perfume, ...]:
        query = "SELECT * FROM perfumes ORDER BY perfume_id LIMIT ? OFFSET ?"
        rows = self.connection.execute(query, (limit, offset)).fetchall()
        return tuple(_row_to_perfume(row) for row in rows)


def _load_schema_sql(schema_path: str | None) -> str:
    if schema_path:
        return Path(schema_path).read_text(encoding="utf-8")
    default_path = Path(__file__).with_name("schema.sql")
    return default_path.read_text(encoding="utf-8")


def _perfume_to_row(perfume: Perfume) -> dict[str, object]:
    payload = asdict(perfume)
    payload["gender_tags"] = _dump_list(perfume.gender_tags)
    payload["scent_families"] = _dump_list(perfume.scent_families)
    payload["molecule_tags"] = _dump_list(perfume.molecule_tags)
    payload["notes_top"] = _dump_list(perfume.notes_top)
    payload["notes_middle"] = _dump_list(perfume.notes_middle)
    payload["notes_base"] = _dump_list(perfume.notes_base)
    payload["notes_all"] = _dump_notes_all(perfume)
    payload["image_urls"] = _dump_list(perfume.image_urls)
    payload["last_scraped_at"] = _dump_datetime(perfume.last_scraped_at)
    return payload


def _row_to_perfume(row: sqlite3.Row) -> Perfume:
    return Perfume(
        perfume_id=row["perfume_id"],
        name=row["name"],
        url=row["url"],
        price_min=row["price_min"],
        price_max=row["price_max"],
        gender_tags=_load_list(row["gender_tags"]),
        scent_families=_load_list(row["scent_families"]),
        molecule_tags=_load_list(row["molecule_tags"]),
        notes_top=_load_list(row["notes_top"]),
        notes_middle=_load_list(row["notes_middle"]),
        notes_base=_load_list(row["notes_base"]),
        description=row["description"],
        image_urls=_load_list(row["image_urls"]),
        last_scraped_at=_load_datetime(row["last_scraped_at"]),
    )


def _dump_list(values: tuple[str, ...]) -> str:
    return json.dumps(list(values), ensure_ascii=True)


def _load_list(raw_value: str) -> tuple[str, ...]:
    parsed = json.loads(raw_value)
    return tuple(str(item) for item in parsed)


def _dump_notes_all(perfume: Perfume) -> str:
    return json.dumps([asdict(item) for item in perfume.notes_all], ensure_ascii=True)


def _dump_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _load_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


_UPSERT_SQL = """
INSERT INTO perfumes (
    perfume_id, name, url, price_min, price_max,
    gender_tags, scent_families, molecule_tags,
    notes_top, notes_middle, notes_base, notes_all,
    description, image_urls, last_scraped_at, updated_at
) VALUES (
    :perfume_id, :name, :url, :price_min, :price_max,
    :gender_tags, :scent_families, :molecule_tags,
    :notes_top, :notes_middle, :notes_base, :notes_all,
    :description, :image_urls, :last_scraped_at, CURRENT_TIMESTAMP
)
ON CONFLICT(perfume_id) DO UPDATE SET
    name = excluded.name,
    url = excluded.url,
    price_min = excluded.price_min,
    price_max = excluded.price_max,
    gender_tags = excluded.gender_tags,
    scent_families = excluded.scent_families,
    molecule_tags = excluded.molecule_tags,
    notes_top = excluded.notes_top,
    notes_middle = excluded.notes_middle,
    notes_base = excluded.notes_base,
    notes_all = excluded.notes_all,
    description = excluded.description,
    image_urls = excluded.image_urls,
    last_scraped_at = excluded.last_scraped_at,
    updated_at = CURRENT_TIMESTAMP;
"""
