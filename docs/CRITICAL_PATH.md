# tsx critical path

**Last updated:** 2026-10-16 · **Prior:** P0–P2 + wx surface **done** (tsx#1–#25)  
**Plan:** [FEEDS.md](FEEDS.md) · **Status:** [STATUS.md](STATUS.md) · **CLI:** `query/tsx_cli.py help`

## Policy
**Depth first, then breadth.** Stay inside 2 GB active / 20 GB archive. New source ⇒ acquire + `run_*.sh` + view + CLI + FEEDS.md row.

---

## Priority order

```
  D1  wx.noaa history backfill (IEM / NWS)     ← depth
  D2  eq.usgs all_month + historical CSV
  D3  wx.noaa.alerts retention (sev≥2)
  D4  pinksheet full monthly history
  D5  news.bbc 1y text-only window
  B1  ECB FX daily
  B2  FRED macro series
  B3  CDC FluView weekly
  B4  Open-Meteo only if D1 history thin
  B5  UST yield curve
```

| Rank | Work | Grain | License | Caps (act/arch) | Ticket |
|------|------|-------|---------|-----------------|--------|
| **D1** | wx history backfill | 5-min→hourly | NWS / IEM | 150M / 1G | *(open)* |
| **D2** | eq history | event | USGS | 250M / 2G | *(open)* |
| **D3** | alerts retention | event | NWS | 100M / 500M | *(open)* |
| **D4** | pinksheet history | month | WB CC BY 4.0 | 50M / 200M | *(open)* |
| **D5** | bbc window | event | BBC RSS | 50M / 200M | *(open)* |
| B1–B5 | breadth set | day/week/month | open | see FEEDS.md | *(after D)* |

## Done (do not reopen)
P0 schema/acquire/load/caps · P1 replica+archive+replay · P2 views/CLI/second stream ·  
wx stations/metrics/alerts/meta/feels/wxnow/near/compare/correlate/rollup ·  
unified job · NWS retry · export-all · health · make test · CI · #1–#25

## Ops
| Job | Cron |
|-----|------|
| USGS acquire | `:43` |
| wx hourly | `:20` |
| alerts | `*/15` |
| caps | `:17` |
| archive all streams | `27 3 * * *` |

**Health:** `tools/wx_health.sh` · **Tests:** `make test` (CI green)
