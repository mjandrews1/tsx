#!/usr/bin/env python3
"""NWS active weather alerts — wx.noaa.alerts (tsx#8)."""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "tsx-geodata/0.1 (+tsx research; contact: mark@local)"
FEED = "https://api.weather.gov/alerts/active?status=actual"


def fetch(url: str) -> dict:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/geo+json"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main() -> int:
    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / "wx.noaa.alerts.jsonl"
    now = datetime.now(timezone.utc).isoformat()
    try:
        fc = fetch(FEED)
    except Exception as e:
        print(json.dumps({"stream": "wx.noaa.alerts", "error": str(e), "at": now}))
        return 1
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for feat in fc.get("features") or []:
            p = feat.get("properties") or {}
            aid = p.get("id") or feat.get("id") or ""
            if not aid:
                continue
            sev = (p.get("severity") or "none").lower()
            sev_val = {"extreme": 5, "severe": 4, "moderate": 3, "minor": 2, "unknown": 1}.get(sev, 0)
            ev = {
                "stream_id": "wx.noaa.alerts",
                "nat_key": f"alert|{aid}",
                "ts_utc": p.get("sent") or p.get("effective") or now,
                "ts_event_utc": p.get("onset") or p.get("effective") or "",
                "ts_ingested_utc": now,
                "value": float(sev_val),
                "unit": "sev",
                "title": (p.get("event") or "alert")[:120],
                "place": (p.get("areaDesc") or "")[:80],
                "url": "https://api.weather.gov/alerts/active",
                "attrib": "NOAA/NWS api.weather.gov",
                "text": (p.get("headline") or p.get("description") or "")[:160],
            }
            fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
            n += 1
    print(json.dumps({"stream": "wx.noaa.alerts", "staged": n, "file": str(out), "at": now}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
