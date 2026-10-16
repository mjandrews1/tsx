#!/usr/bin/env python3
"""NWS station metadata — wx.noaa.meta (tsx#9).

For each STATIONS id: name + lat/lon from api.weather.gov/stations/{id}.
Emits JSONL rows for load_cdb2 (nat_key meta|ST|name / |lat / |lon).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from noaa_obs import STATIONS  # noqa: E402

UA = "tsx-geodata/0.1 (+tsx research; contact: mark@local)"


def fetch(url: str) -> dict:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/geo+json"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main() -> int:
    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / "wx.noaa.meta.jsonl"
    now = datetime.now(timezone.utc).isoformat()
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for st in STATIONS:
            try:
                fc = fetch(f"https://api.weather.gov/stations/{st}")
            except Exception as e:
                print(f"WARN {st}: {e}", file=sys.stderr)
                continue
            p = fc.get("properties") or {}
            name = (p.get("name") or st)[:80]
            loc = (p.get("location") or {}).get("coordinates") or [None, None]
            lon, lat = loc[0], loc[1]
            base = {
                "stream_id": "wx.noaa.meta",
                "ts_utc": now,
                "ts_event_utc": now,
                "ts_ingested_utc": now,
                "unit": "",
                "title": "",
                "place": st,
                "lat": lat,
                "lon": lon,
                "url": f"https://api.weather.gov/stations/{st}",
                "attrib": "NOAA/NWS api.weather.gov",
                "text": "",
            }
            for kind, val, unit in (
                ("name", name, ""),
                ("lat", lat, "deg"),
                ("lon", lon, "deg"),
            ):
                if val is None:
                    continue
                ev = dict(base)
                ev["nat_key"] = f"meta|{st}|{kind}"
                ev["value"] = 0.0 if kind == "name" else float(val)
                ev["unit"] = unit
                ev["title"] = f"{st} {kind}"
                ev["text"] = name if kind == "name" else ""
                fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
                n += 1
    print(json.dumps({"stream": "wx.noaa.meta", "staged": n, "file": str(out), "at": now}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
