-- tsx schema for Comdb2 testdb (U01)
-- Comdb2 notes: INTEGER PRIMARY KEY only; CREATE INDEX / UNIQUE / composite PK
-- rejected here (dyns_load_schema_string). Use tsx_nat_index / tsx_timebucket
-- as lookup/correlation tables instead of secondary indexes.

CREATE TABLE tsx_stream (
  id INTEGER PRIMARY KEY,
  stream_id TEXT,
  title TEXT,
  source_url TEXT,
  grain TEXT,
  active_cap_gb REAL,
  archive_cap_gb REAL
);

CREATE TABLE tsx_series (
  id INTEGER PRIMARY KEY,
  stream_id TEXT,
  code TEXT,
  title TEXT
);

CREATE TABLE tsx_observation (
  id INTEGER PRIMARY KEY,
  stream_id TEXT,
  series_id INTEGER,
  ts_utc TEXT,
  ingested_at TEXT,
  nat_key TEXT,
  value REAL,
  unit TEXT,
  payload_json TEXT
);

CREATE TABLE tsx_nat_index (
  id INTEGER PRIMARY KEY,
  stream_id TEXT,
  nat_key TEXT,
  obs_id INTEGER
);

CREATE TABLE tsx_timebucket (
  id INTEGER PRIMARY KEY,
  bucket_utc TEXT,
  stream_id TEXT,
  nat_key TEXT,
  ts_utc TEXT,
  value REAL
);

CREATE TABLE tsx_lookup (
  id INTEGER PRIMARY KEY,
  stream_id TEXT,
  nat_key TEXT,
  obs_id INTEGER
);
