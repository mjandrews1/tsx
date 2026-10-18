#!/usr/bin/env python3
"""B3: CDC FluView ILI (Influenza-Like Illness).

Source: CDC FluView (public domain, US Government).
URL: https://gis.cdc.gov/grasp/fluview/fluportaldashboard

Grain: week. License: Public domain.
"""
from __future__ import annotations
import csv, io, json, os, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

# CDC FluView ILI CSV (national)
URL = "https://gis.cdc.gov/grasp/fluview/fluportaldashboard/DownloadCsvAll"
ATTRIB = "CDC FluView (public domain)"

def fetch() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": "tsx-health/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def main() -> int:
    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / "health.fluview.jsonl"
    now = datetime.now(timezone.utc).isoformat()

    try:
        csv_text = fetch()
    except Exception as e:
        print(json.dumps({"stream": "health.fluview", "status": "fetch_error", "error": str(e), "at": now}))
        return 1

    n = 0
    reader = csv.DictReader(io.StringIO(csv_text))
    with out.open("w", encoding="utf-8") as fh:
        for row in reader:
            # CDC CSV columns vary; look for common patterns
            week = row.get("YEAR") or row.get("year") or ""
            wkn = row.get("WEEK") or row.get("week") or ""
            ili = row.get("ILITOTAL") or row.get("ilitotal") or row.get("% WEIGHTED ILI") or ""
            if not week or not wkn:
                continue
            try:
                val = float(ili) if ili not in ("", ".") else 0.0
            except ValueError:
                val = 0.0
            ts = f"{week}-W{int(wkn):02d}"
            ev = {
                "stream_id": "health.fluview",
                "nat_key": f"fluview|{week}|{wkn}",
                "ts_utc": f"{week}-{int(wkn):02d}-01T00:00:00+00:00",
                "value": val,
                "unit": "ili_pct",
                "title": f"FluView ILI {week}-W{wkn}",
                "url": "https://gis.cdc.gov/grasp/fluview/fluportaldashboard",
                "attrib": ATTRIB,
            }
            fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
            n += 1

    print(json.dumps({"stream": "health.fluview", "rows": n, "file": str(out), "attrib": ATTRIB, "at": now}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
