# tsx status (2026-10-16)

## P0–P2 (demo pipeline)
| Item | State |
|------|--------|
| Schema + views | **live** `sql/schema.sql` · `views/v_last.sql` |
| Acquire USGS all_day/all_week | **cron** `:43` |
| Load JSONL idempotent | **load_cdb2.py** via `tsx_nat_index` |
| Caps + archive | **cron** `:17` · `27 3 * * *` all streams |
| Replica U02 | **verified** counts match |
| Terminal CLI + views | **tsx_cli.py** + `v_last*` / `v_stats*` / `v_hourly_wx` / `v_daily_wx` |

## wx surface (tsx#6–#22)
32 NWS stations · temp/wind/pressure/RH/dewpoint · alerts · meta ·
`wxnow` `wxfeels` `wxday` `wxrollup` `wxextremes` `near` `compare` `correlate` ·
unified `run_wx_hourly.sh` + `*/15` alerts · NWS retry/backoff.

## Commands
See `docs/TOOLSET.md`.
