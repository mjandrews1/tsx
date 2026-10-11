-- Time-correlation index (bucket by UTC hour)
-- Comdb2: INTEGER PK only (no CREATE INDEX on this cluster)
CREATE TABLE tsx_timebucket (
  id INTEGER PRIMARY KEY,
  bucket_utc TEXT,
  stream_id TEXT,
  nat_key TEXT,
  ts_utc TEXT,
  value REAL
);
-- Manual maps: bucket id = hash31(bucket_utc)
-- Loader writes one row per observation into tsx_timebucket
-- Query: WHERE bucket_utc BETWEEN '2026-10-11T00' AND '2026-10-11T23'
