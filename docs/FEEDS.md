# tsx feed plan — depth first, then breadth

**Draft 2026-10-16** · policy: grow **depth** on live streams before adding sources.  
**Caps:** active **2 GB** (U01 Comdb2) · archive **20 GB** (U02 coldstore).  
**Catalog:** `tsx_stream` / `tsx_series` / `tsx_observation` · idempotent `nat_key` · archive-then-delete.

---

## 1. Depth (first) — deepen what we already have

| Rank | Feed / job | Grain | License | Active cap | Archive cap | Notes |
|-----:|------------|-------|---------|------------|-------------|-------|
| **D1** | **wx.noaa history backfill** | 5-min obs → hourly rollup | **Public domain** (US NWS) | 150 MB | 1 GB | NWS `stations/{id}/observations` is short-window; use `api.weather.gov` + optional **Iowa State IEM** (free, CC) for multi-year point obs. Keep 32 stations; store hourly min/avg/max if 5-min is too dense. |
| **D2** | **eq.usgs longer window** | event | **Public domain** (USGS) | 250 MB | 2 GB | `all_month` + historical CSV (USGS comprehensive). Backfill **one archive pass**, not hourly forever. |
| **D3** | **wx.noaa.alerts retention** | event | **Public domain** (NWS) | 100 MB | 500 MB | Keep severity ≥2; archive daily; purge closed alerts >180d from active. |
| **D4** | **px.wb.pinksheet history** | month | **CC BY 4.0** (World Bank) | 50 MB | 200 MB | Full pink-sheet series backfill (decades of monthly points). |
| **D5** | **news.bbc depth** | event | **BBC RSS — non-commercial / attribution** | 50 MB | 200 MB | Store title+summary only (no media); 1y window. |

**Depth subtotal (archive):** ~4 GB · **active:** ~600 MB → well under 2 / 20 GB.

---

## 2. Breadth (after D1–D5) — new streams

| Rank | Feed | Grain | License | Active | Archive | Value |
|-----:|------|-------|---------|--------|---------|-------|
| **B1** | **FX rates** (ECB daily reference) | day | **ECB / free** (attribution) | 20 MB | 150 MB | Second “market-like” stream; validates catalog + daily grain. |
| **B2** | **FRED macro** (e.g. CPI, UNRATE, DFF) | month/day | **FRED / public** (attribution) | 50 MB | 300 MB | Macro series; aligns with Bloomberg-like terminal. |
| **B3** | **CDC FluView** ILI | week | **Public domain** (US Gov) | 20 MB | 100 MB | Weekly disease signal (pairs with MeshGraph later). |
| **B4** | **Open-Meteo archive** (if NWS history thin) | hour | **CC BY 4.0** | 200 MB | 1.5 GB | Global point history without API key — only if D1 IEM is insufficient. |
| **B5** | **US Treasury yield curve** | day | **Public domain** | 20 MB | 150 MB | Rates depth for terminal. |

**Breadth subtotal (archive):** ~2.2 GB.

---

## 3. Rate / quota policy (per source)

| Source | Budget | Backoff |
|--------|--------|---------|
| api.weather.gov | ≤1 req / 2 s (NWS guideline) | `nws_fetch` retry |
| USGS feeds | 1 fetch / hour (cron) | single-shot daily for month CSV |
| ECB / FRED / CDC | ≤1 / day or month | cache JSONL in staging |

---

## 4. What we will not add (for now)

- Paid / API-key market data
- High-frequency tick (would blow 2 GB active)
- Video / images (BBC)
- Anything without a clear license row

---

## 5. Success metrics

- D1–D5: archive ≤4 GB · active ≤600 MB · `wx_health` / `make test` still green  
- Each new stream: one `acquire/` + `load/run_*.sh` + `v_*` view + CLI verb + `FEEDS.md` row  
- Caps never exceeded without a logged decision (README policy)
