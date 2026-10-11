-- tsx Comdb2 schema (demo: USGS earthquakes)
-- Apply on U01 primary; replicate to U02.

CREATE TABLE stream (
  stream_id      VARCHAR(32)  NOT NULL,
  title          VARCHAR(128) NOT NULL,
  source_url     VARCHAR(512) NOT NULL,
  grain          VARCHAR(16)  NOT NULL,
  active_cap_gb  DECIMAL(6,2) NOT NULL DEFAULT 2.0,
  archive_cap_gb DECIMAL(6,2) NOT NULL DEFAULT 20.0,
  created_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (stream_id)
)$$

CREATE TABLE series (
  series_id  BIGINT       NOT NULL,
  stream_id  VARCHAR(32)  NOT NULL,
  code       VARCHAR(64)  NOT NULL,
  title      VARCHAR(128),
  PRIMARY KEY (series_id)
)$$

CREATE INDEX series_stream_code ON series(stream_id, code)$$

CREATE TABLE observation (
  stream_id    VARCHAR(32)  NOT NULL,
  series_id    BIGINT       NOT NULL,
  ts_utc       DATETIME     NOT NULL,
  ingested_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
  nat_key      VARCHAR(64)  NOT NULL,
  value        DOUBLE,
  unit         VARCHAR(16),
  payload_json VARCHAR(8000),
  PRIMARY KEY (stream_id, nat_key)
)$$

CREATE INDEX obs_stream_ts ON observation(stream_id, ts_utc)$$
CREATE INDEX obs_series_ts ON observation(series_id, ts_utc)$$

INSERT INTO stream(stream_id, title, source_url, grain, active_cap_gb, archive_cap_gb)
VALUES (
  'eq.usgs',
  'USGS Earthquakes',
  'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson',
  'event',
  2.0,
  20.0
)$$
