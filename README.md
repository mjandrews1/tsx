# tsx — time-series exchange

Open foundation for a **Bloomberg-like** terminal: acquire, relationally model, store, and replicate **regular public datastreams** in **Comdb2**, with explicit **space caps** for active vs archive.

**Status:** 2026-10-11 — scaffolding. Demo domain: **USGS earthquakes** (small, free, measurable, time-stamped).

## Why Comdb2

Already deployed on **U01 + U02** (`/opt/bb`, pmux, cluster `utility-02`). SQL + clustered replication for multi-host “exchange” style access. Not the M stack; this is the **SQL plane**.

## Demo scope (deliberately small)

| In | Out (for now) |
|----|----------------|
| One stream: USGS earthquake GeoJSON | Multi-stream federation |
| Relational schema + time-series queries | Full market data / entitlements |
| Ingest + archive job + space caps | Real-time trading UI |
| Simple CLI / SQL reports | Full terminal frontend |

## Candidate streams (later)

Geophysical (quakes, weather, oceans/tides), flora/fauna, disease, social/crime, news, **stocks**, money supply, conflict/wear — all **measurable** and time-indexed.

## Space caps (policy)

| Tier | Cap (demo) | Host | Purpose |
|------|------------|------|---------|
| **Active** | **2 GB** Comdb2 DB | U01 (+ U02 replica) | Hot rows, indexes, last N months |
| **Archive** | **20 GB** files | U02 `coldstore/tsx` | Full history dumps (CSV/Parquet/JSONL) |
| **Working /tmp** | avoid | — | U02 `/tmp` is tmpfs only |

Overage → **archive-then-delete** oldest active rows; never exceed cap without a logged decision.

## Layout

```
docs/DESIGN.md      data model + ingest
docs/CRITICAL_PATH.md
sql/schema.sql      Comdb2 DDL
acquire/usgs_quakes.py
tools/cap_check.sh
```

## Hosts

| Host | Role |
|------|------|
| U01 | Comdb2 primary ingest + SQL |
| U02 | Comdb2 replica + **cold archive** |
| Mac | clients / notebooks |

## License
Open source (add LICENSE when publishing first release). Data from **USGS** (public domain / attribution as required).

## Archive / replay (tsx#4 #5)

- Nightly `tools/archive_cdb2.py testdb 90 $HOME/coldstore/tsx` (cron `27 3 * * *`)
- `tools/replay_archive.py --verify DIR` — count gzip rows
- U01/U02 Comdb2 `testdb` counts match (replica); coldstore holds >90d rows
