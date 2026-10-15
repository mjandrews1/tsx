#!/usr/bin/env python3
"""NOAA NWS station observations (hourly) — wx.noaa.

Source: api.weather.gov (NWS). License: US Government / NWS data.
Policy: temperature + wind + pressure per station observation; no bodies.
User-Agent required by NWS.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# A few CONUS + AK/HI coverage points (NWS station IDs)
STATIONS = ["KLGA", "KSFO", "KORD", "KSEA", "KATL", "PHNL"]
UA = "tsx-geodata/0.1 (+tsx research; contact: mark@local)"
FEED = "https://api.weather.gov/stations/{st}/observations?limit=16"


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/geo+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main() -> int:
    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / "wx.noaa.obs.jsonl"
    now = datetime.now(timezone.utc).isoformat()
    n = err = 0
    with out.open("a", encoding="utf-8") as fh:
        for st in STATIONS:
            try:
                fc = fetch(FEED.format(st=st))
            except Exception as e:
                err += 1
                print(f"WARN {st}: {e}", file=sys.stderr)
                continue
            for feat in fc.get("features") or []:
                p = feat.get("properties") or {}
                ts = p.get("timestamp") or ""
                if not ts:
                    continue
                temp = ((p.get("temperature") or {}).get("value"))
                # NWS SI: C, m/s, Pa — store temp as value when present
                if temp is None:
                    continue
                ev = {
                    "stream_id": "wx.noaa",
                    "nat_key": f"noaa|{st}|{ts}",
                    "ts_utc": ts,
                    "ts_event_utc": ts,
                    "ts_ingested_utc": now,
                    "value": float(temp),
                    "unit": "C",
                    "title": f"{st} temperature",
                    "place": st,
                    "lat": ((p.get("location") or {}).get("coordinates") or [None, None])[1],
                    "lon": ((p.get("location") or {}).get("coordinates") or [None, None])[0],
                    "url": f"https://api.weather.gov/stations/{st}/observations",
                    "attrib": "NOAA/NWS api.weather.gov",
                    "wind_mps": ((p.get("windSpeed") or {}).get("value")),
                    "press_pa": ((p.get("barometricPressure") or {}).get("value")),
                    "text": (p.get("textDescription") or "")[:120],
                }
                fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
                n += 1
    print(json.dumps({
        "stream": "wx.noaa", "staged": n, "errors": err,
        "stations": STATIONS, "file": str(out), "at": now,
    }))
    return 0 if err < len(STATIONS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
