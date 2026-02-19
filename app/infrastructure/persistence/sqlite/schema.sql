PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS perfumes (
    perfume_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    price_min REAL,
    price_max REAL,
    gender_tags TEXT NOT NULL DEFAULT '[]',
    scent_families TEXT NOT NULL DEFAULT '[]',
    molecule_tags TEXT NOT NULL DEFAULT '[]',
    notes_top TEXT NOT NULL DEFAULT '[]',
    notes_middle TEXT NOT NULL DEFAULT '[]',
    notes_base TEXT NOT NULL DEFAULT '[]',
    notes_all TEXT NOT NULL DEFAULT '[]',
    description TEXT NOT NULL DEFAULT '',
    image_urls TEXT NOT NULL DEFAULT '[]',
    last_scraped_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (price_min IS NULL OR price_min >= 0),
    CHECK (price_max IS NULL OR price_max >= 0),
    CHECK (price_min IS NULL OR price_max IS NULL OR price_min <= price_max)
);

CREATE INDEX IF NOT EXISTS idx_perfumes_name ON perfumes(name);
CREATE INDEX IF NOT EXISTS idx_perfumes_last_scraped_at ON perfumes(last_scraped_at);
