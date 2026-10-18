#!/usr/bin/env python3
"""B1: ECB daily FX reference rates.

Source: ECB Statistical Data Warehouse (free, attribution required).
URL: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml

Grain: day. License: ECB — attribution required.
"""
from __future__ import annotations
import json, os, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ATTRIB = "European Central Bank"

def main() -> int:
    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    stage.mkdir(parents=True, exist_ok=True)
    out = stage / "fx.ecb.jsonl"
    now = datetime.now(timezone.utc).isoformat()

    req = urllib.request.Request(URL, headers={"User-Agent": "tsx-fin/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        xml_text = r.read().decode("utf-8", "replace")

    root = ET.fromstring(xml_text)
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for date_cube in root.iter():
            # date Cube has 'time' attribute
            if "time" not in date_cube.attrib or "currency" in date_cube.attrib:
                continue
            date = date_cube.attrib["time"]
            for cur_cube in date_cube:
                if "currency" not in cur_cube.attrib:
                    continue
                cur = cur_cube.attrib["currency"]
                rate = float(cur_cube.attrib.get("rate", "0"))
                ev = {
                    "stream_id": "fx.ecb",
                    "nat_key": f"ecb|{cur}|{date}",
                    "ts_utc": f"{date}T00:00:00+00:00",
                    "value": rate,
                    "unit": f"EUR/{cur}",
                    "title": f"EUR/{cur} {date}",
                    "url": URL,
                    "attrib": ATTRIB,
                }
                fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
                n += 1

    print(json.dumps({"stream": "fx.ecb", "rows": n, "file": str(out), "attrib": ATTRIB, "at": now}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
