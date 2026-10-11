# tsx critical path

**Goal:** small, measurable demo of acquire → Comdb2 store → replicate → archive with **space caps**, as the foundation of an open “Bloomberg-like” terminal.

## P0 — demo pipeline (this week)

| # | Work | Status |
|---|------|--------|
| P0.1 | Repo scaffold (README, DESIGN, schema, acquire, cap_check) | **done** |
| P0.2 | Load `sql/schema.sql` on U01 Comdb2 | OPEN |
| P0.3 | Schedule `acquire/usgs_quakes.py` (day + week backfill) | OPEN |
| P0.4 | JSONL → `observation` loader | OPEN |
| P0.5 | Time-series SQL demo (hourly counts / avg mag) | OPEN |
| P0.6 | `tools/cap_check.sh` wired to cron | OPEN |

## P1 — replica + archive

| # | Work | Status |
|---|------|--------|
| P1.1 | Confirm U02 Comdb2 replica healthy | OPEN |
| P1.2 | Nightly archive job (export &gt;90d → `coldstore/tsx`) | OPEN |
| P1.3 | Archive-then-delete under **2 GB active / 20 GB archive** | OPEN |
| P1.4 | Replay-from-archive test | OPEN |

## P2 — terminal surface

| # | Work | Status |
|---|------|--------|
| P2.1 | Views `v_last` / `v_stats` | OPEN |
| P2.2 | `tsx` CLI query | OPEN |
| P2.3 | Second stream (e.g. FX or NOAA) proving the catalog model | OPEN |

## Non-goals (v0)
Market entitlements · trading · live tick UI · multi-region.

## Caps
See README. **U02 `/tmp` is tmpfs — never stage archives there.**
