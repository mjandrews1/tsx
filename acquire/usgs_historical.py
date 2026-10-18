#!/usr/bin/env python3
"""D2: USGS earthquake historical CSV loader.

Loads USGS earthquake CSV data (historical) into staging JSONL.
Source: https://earthquake.usgs.gov/earthquakes/search/ (CSV export)

Usage:
  usgs_historical.py <csv_file> [--min-mag 0.0]

Idempotent by event id. Writes to $TSX_STAGE/eq.usgs.historical.jsonl.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: usgs_historical.py <csv_file> [--min-mag 0.0]", file=sys.stderr)
        return 2

    csv_path = Path(sys.argv[1])
    if not csv_path.is_file():
        print(f"error: {csv_path} not found", file=sys.stderr)
        return 1

    min_mag = 0.0
    if "--min-mag" in sys.argv:
        idx = sys.argv.index("--min-mag")
        if idx + 1 < len(sys.argv):
            min_mag = float(sys.argv[idx + 1])

    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / "eq.usgs.historical.jsonl"
    now = datetime.now(timezone.utc).isoformat()

    n = 0
    skipped = 0
    with csv_path.open(encoding="utf-8", errors="replace") as f, out.open("a", encoding="utf-8") as fh:
        reader = csv.DictReader(f)
        for row in reader:
            # USGS CSV columns: time,latitude,longitude,depth,mag,magType,nst,gap,dmin,rms,net,id,updated,place,type,horizontalError,depthError,magError,magNst,status,locationSource,magSource
            eid = (row.get("id") or "").strip()
            if not eid:
                skipped += 1
                continue
            try:
                mag = float(row.get("mag") or "0")
            except ValueError:
                mag = 0.0
            if mag < min_mag:
                skipped += 1
                continue

            # Convert epoch ms to ISO
            ts_raw = (row.get("time") or "").strip()
            try:
                ts_ms = int(ts_raw)
                ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
            except (ValueError, OSError):
                ts = ""

            try:
                lat = float(row.get("latitude") or "0")
            except ValueError:
                lat = 0.0
            try:
                lon = float(row.get("longitude") or "0")
            except ValueError:
                lon = 0.0
            try:
                depth = float(row.get("depth") or "0")
            except ValueError:
                depth = 0.0

            ev = {
                "stream_id": "eq.usgs",
                "nat_key": eid,
                "ts_utc": ts,
                "value": mag,
                "unit": row.get("magType") or "ml",
                "place": (row.get("place") or "")[:120],
                "lat": lat,
                "lon": lon,
                "depth_km": depth,
                "url": f"https://earthquake.usgs.gov/earthquakes/eventpage/{eid}",
                "title": f"M {mag:.1f} - {(row.get('place') or '')[:100]}",
                "attrib": "USGS earthquake.usgs.gov",
            }
            fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
            n += 1

    print(json.dumps({
        "stream": "eq.usgs.historical",
        "loaded": n,
        "skipped": skipped,
        "min_mag": min_mag,
        "file": str(out),
        "at": now,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
