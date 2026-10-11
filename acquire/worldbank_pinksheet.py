#!/usr/bin/env python3
"""World Bank Commodity Markets (Pink Sheet) — monthly price series.

License: CC BY 4.0 — attribution required. Cite source URL in every row.
https://www.worldbank.org/en/research/commodity-markets
Data: CMO-Historical-Data-Monthly.xlsx (prices & forecasts)

Policy: price observation date only + series code + value + source URL.
No report body. Observation date is the 1st of the month, stored as UTC.

Usage:
  worldbank_pinksheet.py [out.jsonl]
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx"
)
LANDING = "https://www.worldbank.org/en/research/commodity-markets"
ATTRIB = "World Bank, Commodity Markets (Pink Sheet), CC BY 4.0"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "tsx-0.2 (pinksheet; +attribution)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def parse_xlsx(data: bytes):
    """Minimal xlsx reader: first sheet, rows of (date_str, col_name -> value)."""
    import io
    import re
    import zipfile

    z = zipfile.ZipFile(io.BytesIO(data))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        ss = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
        shared = re.findall(r"<t[^>]*>(.*?)</t>", ss, re.S)
    sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8", "replace")
    # cell refs
    rows = {}
    for m in re.finditer(r'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>', sheet, re.S):
        rn = int(m.group(1))
        cells = {}
        for cm in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*)>(.*?)</c>', m.group(2), re.S):
            col, attrs, inner = cm.group(1), cm.group(3), cm.group(4)
            v = re.search(r"<v>(.*?)</v>", inner, re.S)
            val = v.group(1) if v else ""
            if 't="s"' in attrs and val.isdigit():
                val = shared[int(val)] if int(val) < len(shared) else val
            cells[col] = val
        rows[rn] = cells
    return rows


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "wb.pinksheet.jsonl")
    raw = fetch(SOURCE_URL)
    rows = parse_xlsx(raw)
    if not rows:
        print("no rows parsed", file=sys.stderr)
        return 1
    # header at row 4 typically: month, CRUDE_PETRO, ...
    header = rows.get(4) or rows.get(3) or {}
    cols = {c: name for c, name in header.items() if name and c != "A"}
    now = datetime.now(timezone.utc).isoformat()
    n = 0
    with out.open("a", encoding="utf-8") as fh:
        for rn, cells in sorted(rows.items()):
            date_s = cells.get("A", "")
            if not date_s or not re.match(r"^(19|20)\d{2}", str(date_s)):
                continue
            # Excel serial or YYYY or YYYY-MM
            s = str(date_s)
            if re.match(r"^\d{5}(\.\d+)?$", s):
                # excel serial -> date
                serial = int(float(s))
                ts = datetime(1899, 12, 30, tzinfo=timezone.utc).fromtimestamp(
                    (serial - 25569) * 86400, tz=timezone.utc
                ).isoformat()
            else:
                ym = s.split("-")[0]
                ts = f"{ym}-01-01T00:00:00+00:00" if len(s) <= 7 else s
            for col, name in cols.items():
                val = cells.get(col, "")
                if val in ("", "..", "..."):
                    continue
                try:
                    fv = float(val)
                except Exception:
                    continue
                key = f"wb.pinksheet|{name}|{ts[:7]}"
                ev = {
                    "stream_id": "px.wb.pinksheet",
                    "nat_key": key,
                    "ts_utc": ts,
                    "ts_event_utc": ts,
                    "ts_reported_utc": now,
                    "ts_ingested_utc": now,
                    "value": fv,
                    "unit": name,
                    "title": name,
                    "url": SOURCE_URL,
                    "place": LANDING,
                }
                fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
                n += 1
    print(json.dumps({
        "stream": "px.wb.pinksheet",
        "rows": n,
        "file": str(out),
        "source": SOURCE_URL,
        "attribution": ATTRIB,
        "license": "CC BY 4.0",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
