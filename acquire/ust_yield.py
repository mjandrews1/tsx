#!/usr/bin/env python3
"""B5: US Treasury yield curve (daily).

Source: Treasury.gov (public domain).
URL: https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv

Grain: day. License: Public domain.
"""
from __future__ import annotations
import csv, io, json, os, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Treasury daily yield curve CSV (all rates)
URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2024/all?type=daily_treasury_yield_curve&field_tdr_date_value=2024&page&_format=csv"
ATTRIB = "US Department of the Treasury (public domain)"

def fetch() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": "tsx-fin/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def main() -> int:
    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / "rates.ust.jsonl"
    now = datetime.now(timezone.utc).isoformat()

    try:
        csv_text = fetch()
    except Exception as e:
        print(json.dumps({"stream": "rates.ust", "status": "fetch_error", "error": str(e), "at": now}))
        return 1

    n = 0
    reader = csv.DictReader(io.StringIO(csv_text))
    with out.open("w", encoding="utf-8") as fh:
        for row in reader:
            date = (row.get("Date") or row.get("date") or "").strip()
            if not date:
                continue
            # Treasury CSV columns: Date, 1 Mo, 2 Mo, 3 Mo, 4 Mo, 6 Mo, 1 Yr, 2 Yr, 3 Yr, 5 Yr, 7 Yr, 10 Yr, 20 Yr, 30 Yr
            for tenor, val_str in row.items():
                if tenor in ("Date", "date", ""):
                    continue
                val_str = (val_str or "").strip()
                if val_str in ("", "N/A", "."):
                    continue
                try:
                    val = float(val_str)
                except ValueError:
                    continue
                ev = {
                    "stream_id": "rates.ust",
                    "nat_key": f"ust|{tenor}|{date}",
                    "ts_utc": f"{date}T00:00:00+00:00",
                    "value": val,
                    "unit": f"pct_{tenor.replace(' ', '')}",
                    "title": f"UST {tenor} yield {date}",
                    "url": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates",
                    "attrib": ATTRIB,
                }
                fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
                n += 1

    print(json.dumps({"stream": "rates.ust", "rows": n, "file": str(out), "attrib": ATTRIB, "at": now}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
