# tsx design — acquire → model → store → replicate → archive

## 1. Datastream contract

Each stream has:

| Field | Meaning |
|-------|---------|
| `stream_id` | e.g. `eq.usgs`, `wx.noaa`, `px.stooq` |
| `source` | URL / API |
| `grain` | timestamp grain (event / hour / day) |
| `keys` | natural key (e.g. USGS `id`) |
| `unit` | measurable fields + units |

**Must be:** public, legal to store, **measurable**, **time-stamped**.

## 2. Core relational model (star + raw)

```text
stream 1—* series 1—* observation (fact)
              *— dimension (place, magnitude bin, …)
```

### Tables (demo — earthquakes)

```sql
-- catalog
CREATE TABLE stream (
  stream_id     VARCHAR(32) PRIMARY KEY,
  title         VARCHAR(128),
  source_url    VARCHAR(512),
  grain         VARCHAR(16),   -- event|hour|day
  active_cap_gb DECIMAL(6,2),
  archive_cap_gb DECIMAL(6,2),
  created_at    DATETIME
);

CREATE TABLE series (
  series_id     BIGINT PRIMARY KEY,
  stream_id     VARCHAR(32),
  code          VARCHAR(64),   -- e.g. region / magnitude class
  title         VARCHAR(128),
  UNIQUE(stream_id, code)
);

CREATE TABLE observation (
  stream_id     VARCHAR(32),
  series_id     BIGINT,
  ts_utc        DATETIME,      -- event time
  ingested_at   DATETIME,
  nat_key       VARCHAR(64),   -- USGS event id
  value         DOUBLE,        -- primary measure (magnitude)
  unit          VARCHAR(16),   -- mw/ml
  payload_json  VARCHAR(8000), -- trimmed source fields
  PRIMARY KEY (stream_id, nat_key)
);
```

### Time-series query patterns

```sql
-- last 7 days, bucketed
SELECT date_trunc('hour', ts_utc) h, count(*), avg(value), max(value)
FROM observation
WHERE stream_id='eq.usgs' AND ts_utc > now() - INTERVAL '7' DAY
GROUP BY 1 ORDER BY 1;

-- by region (join series.code)
```

Indexes: `(stream_id, ts_utc)`, `(series_id, ts_utc)`, `(nat_key)`.

## 3. Acquire

- Poll public API on a schedule (cron / systemd timer on U01).
- Idempotent upsert on `(stream_id, nat_key)`.
- Write **raw JSONL** to staging before SQL load (audit + replay).

Demo: `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson` (and `all_week` for backfill).

## 4. Replicate

- U01 Comdb2 primary; U02 cluster replica (existing `cluster nodes` + `copycomdb2` setup).
- Readers may query U02; writes only on U01.

## 5. Archive & space caps

| Step | Action |
|------|--------|
| Nightly | Export rows older than **90 days** (demo) to `coldstore/tsx/<stream>/<YYYY-MM>.csv.gz` on U02 |
| After verify | DELETE from active `observation` |
| Weekly | `tools/cap_check.sh` — fail if active &gt; cap or archive &gt; cap |
| Never | Dump to `/tmp` on U02 (tmpfs) |

## 6. Terminal / “Bloomberg” surface (later)

1. SQL views (`v_last`, `v_stats`)  
2. REPL / CLI (`tsx q 'eq last 24h'`)  
3. Optional TUI or web panel (read-only)

## 7. Trust & hygiene

- Cite USGS (and any other source) in UI/metadata.
- No credentials in git; API keys in env if ever required.
- Record ingest errors; no silent drops.
