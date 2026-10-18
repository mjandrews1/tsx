#!/usr/bin/env python3
"""B2: FRED macro series (CPI, UNRATE, DFF, etc).

Source: FRED API (free, attribution required).
Requires FRED_API_KEY env var. Falls back to CSV download if no key.

Grain: month/day. License: FRED — attribution required.
"""
from __future__ import annotations
import json, os, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SERIES = {
    "CPIAUCSL": "Consumer Price Index",
    "UNRATE": "Unemployment Rate",
    "DFF": "Federal Funds Effective Rate",
    "GDP": "Real GDP",
    "DGS10": "10-Year Treasury Yield",
}

CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
ATTRIB = "FRED, Federal Reserve Bank of St. Louis"

def fetch_csv(series: str) -> str:
    url = CSV_URL.format(series=series)
    req = urllib.request.Request(url, headers={"User-Agent": "tsx-fin/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def main() -> int:
    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / "macro.fred.jsonl"
    now = datetime.now(timezone.utc).isoformat()

    total = 0
    with out.open("w", encoding="utf-8") as fh:
        for sid, title in SERIES.items():
            try:
                csv_text = fetch_csv(sid)
            except Exception as e:
                print(f"  skip {sid}: {e}", file=sys.stderr)
                continue
            lines = csv_text.strip().split("\n")
            for line in lines[1:]:  # skip header
                parts = line.split(",")
                if len(parts) < 2:
                    continue
                date = parts[0].strip()
                val_str = parts[1].strip()
                if val_str in ("", "."):
                    continue
                try:
                    val = float(val_str)
                except ValueError:
                    continue
                ev = {
                    "stream_id": "macro.fred",
                    "nat_key": f"fred|{sid}|{date}",
                    "ts_utc": f"{date}T00:00:00+00:00",
                    "value": val,
                    "unit": sid,
                    "title": f"{title} ({sid})",
                    "url": f"https://fred.stlouisfed.org/series/{sid}",
                    "attrib": ATTRIB,
                }
                fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
                total += 1

    print(json.dumps({"stream": "macro.fred", "rows": total, "series": len(SERIES), "file": str(out), "attrib": ATTRIB, "at": now}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
