#!/usr/bin/env python3
"""Acquire USGS earthquake GeoJSON into staging JSONL (SQL load is a later step).

Idempotent by event id. Never writes to /tmp on U02; use $TSX_STAGE or ~/tsx-staging.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FEEDS = {
    "all_day": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
    "all_week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson",
    "all_month": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson",
}


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "tsx-geodata/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def events(fc: dict):
    for feat in fc.get("features") or []:
        p = feat.get("properties") or {}
        g = feat.get("geometry") or {}
        coords = g.get("coordinates") or [None, None, None]
        eid = (feat.get("id") or p.get("code") or "").strip()
        if not eid:
            continue
        ts_ms = p.get("time")
        if ts_ms is None:
            continue
        yield {
            "nat_key": eid,
            "ts_utc": datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).isoformat(),
            "value": p.get("mag"),
            "unit": "mww" if p.get("magType") in (None, "mww") else str(p.get("magType")),
            "place": p.get("place"),
            "lon": coords[0],
            "lat": coords[1],
            "depth_km": coords[2],
            "url": p.get("url"),
            "title": p.get("title"),
        }


def main() -> int:
    feed = sys.argv[1] if len(sys.argv) > 1 else "all_day"
    if feed not in FEEDS:
        print(f"unknown feed {feed}; use one of {list(FEEDS)}", file=sys.stderr)
        return 2
    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / f"eq.usgs.{feed}.jsonl"
    fc = fetch(FEEDS[feed])
    n = 0
    with out.open("a", encoding="utf-8") as fh:
        for e in events(fc):
            fh.write(json.dumps(e, separators=(",", ":")) + "\n")
            n += 1
    print(json.dumps({
        "feed": feed,
        "staged": n,
        "file": str(out),
        "at": datetime.now(timezone.utc).isoformat(),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
