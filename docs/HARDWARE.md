# tsx / home lab hardware (draft)

## Role split (proposed)
| Node | Role |
|------|------|
| U01 | Comdb2 primary + ingest + YDB MeshGraph |
| U02 | Comdb2 replica + coldstore + archive |
| **Mac Mini A (new)** | **Orchestrator** — timers, CI agents, cron, Tailscale funnel |
| **Mac Mini B (new)** | **tsx dedicated** — acquire + Comdb2 `tsxdb` + reports |

## Minimum specs (2026)
| | Orchestrator | tsx node |
|--|--------------|----------|
| CPU | 4–6 cores | 6–8 cores |
| RAM | 16 GB | 32 GB |
| Disk | 512 GB SSD | 1–2 TB NVMe |
| Net | 1 GbE + Tailscale | 1 GbE |
| OS | macOS or Ubuntu 24.04 | Ubuntu 24.04 preferred |

**Intel NUC / older Mac Mini i5–i7 (2018–2020):** fine for orchestrator; tsx wants SSD + 16–32 GB RAM.
