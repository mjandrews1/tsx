#!/usr/bin/env python3
"""D1: wx.noaa historical backfill via IEM ASOS (tsx FEEDS.md).

Fetches hourly temperature (+ wind/pressure if present) for NWS stations
over a date range → JSONL for load_cdb2 (nat_key noaa|ST|ISO-ts).

Usage:
  TSX_STAGE=/home/mark/tsx-staging python3 acquire/wx_history.py --stations KLGA,KBOS --start 2024-01-01 --end 2024-03-01
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

UA = "tsx-geodata/0.1 (+tsx research)"
# IEM uses 3-letter ASOS ids (LGA not KLGA)
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

def k_to_iem(st: str) -> str:
    st = st.upper()
    return st[1:] if st.startswith("K") and len(st) == 4 else st

def fetch_csv(station: str, y1, m1, d1, y2, m2, d2) -> str:
    url = (
        f"{IEM}?station={k_to_iem(station)}&data=tmpc,sknt,mslp"
        f"&year1={y1}&month1={m1}&day1={d1}"
        f"&year2={y2}&month2={m2}&day2={d2}"
        f"&tz=UTC&format=onlycomma&latlon=no&missing=empty&trace=empty"
        f"&report_type=1&report_type=2&report_type=3"
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", "replace")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations", default="KLGA,KBOS,KPHL,KDCA,KBWI,KORD,KMSP,KDET,KCLE,KMCI,KATL,KMCO,KMIA,KRDU,KBNA,KDFW,KIAH,KOKC,KSTL,KDEN,KPHX,KABQ,KSLC,KLAS,KSFO,KLAX,KSEA,KPDX,KSAN,PHNL,PAFA,PANC")
    ap.add_argument("--start", default="2024-10-01")
    ap.add_argument("--end", default="2026-10-16")
    ap.add_argument("--max-stations", type=int, default=0)
    args = ap.parse_args()
    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / "wx.noaa.history.jsonl"
    stations = [s.strip() for s in args.stations.split(",") if s.strip()]
    if args.max_stations:
        stations = stations[: args.max_stations]
    y1, m1, d1 = (int(x) for x in args.start.split("-"))
    y2, m2, d2 = (int(x) for x in args.end.split("-"))
    now = datetime.now(timezone.utc).isoformat()
    total = 0
    with out.open("w", encoding="utf-8") as fh:
        for st in stations:
            try:
                text = fetch_csv(st, y1, m1, d1, y2, m2, d2)
            except Exception as e:
                print(f"WARN {st}: {e}", flush=True)
                continue
            n = 0
            # hourly: keep rows where minute==0 or first non-null tmpc in hour
            seen_hour = set()
            for row in csv.DictReader(io.StringIO(text)):
                ts = (row.get("valid") or "").strip()
                tmpc = (row.get("tmpc") or "").strip()
                if not ts or tmpc == "":
                    continue
                # IEM: "2024-01-01 00:51"
                try:
                    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M")
                except ValueError:
                    continue
                hour = dt.replace(minute=0, second=0, microsecond=0)
                key = hour.isoformat() + "+00:00"
                if key in seen_hour:
                    continue
                seen_hour.add(key)
                try:
                    val = float(tmpc)
                except ValueError:
                    continue
                ev = {
                    "stream_id": "wx.noaa",
                    "nat_key": f"noaa|{st}|{key}",
                    "ts_utc": key,
                    "ts_event_utc": key,
                    "ts_ingested_utc": now,
                    "value": val,
                    "unit": "C",
                    "title": f"{st} temperature (hist)",
                    "place": st,
                    "url": "https://mesonet.agron.iastate.edu/",
                    "attrib": "IEM ASOS / NWS",
                }
                fh.write(__import__("json").dumps(ev, separators=(",", ":")) + "\n")
                n += 1
                total += 1
            print(json_line(st, n), flush=True)
    print({"stream": "wx.noaa", "file": str(out), "stations": len(stations), "rows": total, "at": now})
    return 0

def json_line(st, n):
    import json
    return json.dumps({"station": st, "staged": n})

if __name__ == "__main__":
    raise SystemExit(main())
