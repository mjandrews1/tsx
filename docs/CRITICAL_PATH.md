# tsx critical path

**Last updated:** 2026-10-16 · **Status:** P0–P2 done · wx surface live

## Done
| Track | Tickets |
|-------|---------|
| P0 demo pipeline | #1 |
| P1 replica + archive | #2 #4 #5 #19 |
| P2 terminal + second stream | #3 |
| wx stations/metrics/alerts/meta | #6–#9 |
| wx CLI (feels, now, near, compare, correlate, rollup) | #10–#17 #20 #22 |
| ops (unified job, NWS retry, health, tests, CI) | #14 #18 #21 #23 #24 #25 |

## Live surface
- **Streams:** eq.usgs · wx.noaa (32 stations) · wx.noaa.alerts · wx.noaa.meta · px.wb.pinksheet · news.bbc
- **Cron:** `:43` USGS · `:20` wx_hourly · `*/15` alerts · `:17` caps · `27 3` archive
- **CLI:** `query/tsx_cli.py help` · **Health:** `tools/wx_health.sh` · **Tests:** `make test`

## Optional later
- Historical wx backfill (NWS window limited)
- Alert→city geocode
- Grafana / dashboard
