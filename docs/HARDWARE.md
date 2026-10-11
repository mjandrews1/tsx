# tsx hardware (budget / 2014-era)

**Constraint (user):** ~2014-era machines · **tsx: 8 GB RAM + 1 TB storage** · orchestrator **smaller** · price-limited **per machine** and **total**.

## Role map (minimum viable)

| Node | Use | Target |
|------|-----|--------|
| **U01 / U02** | Comdb2 + YDB (already owned) | keep |
| **tsx box** | acquire + `tsxdb` + archive staging | **8 GB / 1 TB** |
| **orchestrator** | cron, backup, Tailscale funnel, CI agent | **4–8 GB / 256–500 GB** |

One extra box can do **both** roles if the budget is one machine: put timers + Comdb2 on the same Mini (demo scale).

## Preferred vintage (best $/core)

| Model | CPU | Notes |
|-------|-----|--------|
| **Mac Mini 2012 (A1347) Quad i7** | i7-3610QM / 3630QM class **4 cores** | **Best pick** for Comdb2 under $ constraints |
| **Mac Mini 2014 (A1347)** | i5-42xx / i7-4578U **dual core** | OK for demo; prefer i7/3.0 GHz |
| **Intel NUC / mini PC ~2013–2015** | i5-4xxx / i7-4xxx | Often cheaper; 2.5" or mSATA SSD |
| **2010 Mini** | Core 2 Duo | Orchestrator only |

## Profiles

### tsx node (minimum)
- CPU: dual i7 (2014) or **quad i7 (2012)**
- RAM: **8 GB** (not 4)
- Disk: **1 TB** — enough for **2 GB active + 20 GB archive** + OS
- Prefer **SSD** (or cheap SSD + HDD if chassis allows); SATA SSD is fine
- Net: 1 GbE

### Orchestrator (minimum)
- CPU: dual core 2010–2014
- RAM: **4 GB** (8 if free)
- Disk: 256–500 GB HDD/SSD
- Jobs: cron, `cap_check`, rsync to coldstore, Tailscale

## Budget tactics
- Buy **2012 quad** before **2014 dual** at the same price
- 8 GB SKU beats 4 GB SKU even if slightly older
- Factor PSU/SSD/RAM upgrade + shipping into **total**
- Skip unibody MacBooks with dead batteries for headless use

## What this still demos
USGS hourly/day feed → Comdb2 → hourly stats → cap/archival. Not a full market stack.

## Deploy note
Keep **U02 `/tmp`** out of archive paths (tmpfs). See `tools/cap_check.sh`.
