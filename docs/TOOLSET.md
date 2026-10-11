# tsx toolset

| Layer | Choice | Notes |
|-------|--------|-------|
| Store | Comdb2 (U01 primary, U02 replica) | Already on hosts |
| Acquire | Python 3 stdlib | `acquire/usgs_quakes.py` |
| Schedule | systemd timer / cron on U01 | |
| Validate | SQL + small Python | duplicates, nulls, counts |
| Staging | JSONL under `$TSX_STAGE` or `~/tsx-staging` | **not** U02 `/tmp` (tmpfs) |
| Load | `csql2` / comdb2 CLI | idempotent upsert |
| Caps | `tools/cap_check.sh` | 2 GB active / 20 GB archive |
| Archive | `.csv.gz` / `.jsonl.gz` in `coldstore/tsx/YYYY-MM` | |
| Views / CLI | SQL views + thin `tsx` CLI | Plotly/textual later |
| CI | Actions: syntax + dry-run acquire + cap_check | |

**Skip in v0:** Kafka, k8s, Influx/Timescale (Comdb2 is the store), big BI.
