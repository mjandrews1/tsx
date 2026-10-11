#!/usr/bin/env python3
"""World Bank Commodity Markets (Pink Sheet) — monthly spot-style prices.

License: **CC BY 4.0** — attribution required on every row.
Source: https://www.worldbank.org/en/research/commodity-markets
Workbook: CMO-Historical-Data-Monthly.xlsx → sheet **Monthly Prices**

Includes **fertilizers**: DAP, TSP, urea, phosphate rock, potash
(spot descriptions in sheet Description / shared strings).

Policy: observation month → UTC; value + series name + source URL. No bodies.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
import zipfile
import io
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx"
)
LANDING = "https://www.worldbank.org/en/research/commodity-markets"
ATTRIB = "World Bank, Commodity Markets (Pink Sheet), CC BY 4.0"

# fertilizer + energy + metals focus for tsx
WANTED = re.compile(
    r"urea|dap|tsp|phosphate|potash|potassium|fertil|crude|petroleum|brent|wti|coal|"
    r"natural gas|copper|aluminum|aluminium|nickel|zinc|lead|tin|iron|gold|silver|"
    r"platinum|palladium",
    re.I,
)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "tsx-0.3 (pinksheet; +attribution)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def load_sheet(data: bytes, sheet_path: str = "xl/worksheets/sheet2.xml"):
    z = zipfile.ZipFile(io.BytesIO(data))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        ss = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
        shared = re.findall(r"<t[^>]*>(.*?)</t>", ss, re.S)
    sheet = z.read(sheet_path).decode("utf-8", "replace")
    rows = {}
    for m in re.finditer(r'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>', sheet, re.S):
        rn = int(m.group(1))
        cells = {}
        for cm in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*)>(.*?)</c>', m.group(2), re.S):
            col, attrs, inner = cm.group(1), cm.group(3), cm.group(4)
            v = re.search(r"<v>(.*?)</v>", inner, re.S)
            val = v.group(1) if v else ""
            if 't="s"' in attrs and val.isdigit() and int(val) < len(shared):
                val = shared[int(val)]
            cells[col] = val
        rows[rn] = cells
    return rows


def month_to_utc(period: str) -> str:
    """2020M09 or 2020-09 or 2020 -> UTC ISO on the 1st."""
    period = str(period).strip()
    m = re.match(r"^(\d{4})M(\d{2})$", period)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01T00:00:00+00:00"
    m = re.match(r"^(\d{4})-(\d{2})$", period)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01T00:00:00+00:00"
    m = re.match(r"^(\d{4})$", period)
    if m:
        return f"{m.group(1)}-01-01T00:00:00+00:00"
    return ""


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "wb.pinksheet.jsonl")
    rows = load_sheet(fetch(SOURCE_URL))
    if not rows:
        print("no rows", file=sys.stderr)
        return 1
    # Monthly Prices: row 5 has series names in C+; row 6 units; data from row 7
    header = {}
    header_rn = 0
    for rn in sorted(rows):
        cells = rows[rn]
        # first row with several string labels in C+ and no A date
        labels = [v for c, v in cells.items() if c != "A" and isinstance(v, str) and v and not v.startswith("$") and not re.match(r"^\(", v)]
        if len(labels) >= 5:
            header = cells
            header_rn = rn
            break
    if not header:
        print("header not found", file=sys.stderr)
        return 1
    cols = {c: str(v).strip() for c, v in header.items() if c not in ("A", "B") and v}
    now = datetime.now(timezone.utc).isoformat()
    n = fert = 0
    with out.open("a", encoding="utf-8") as fh:
        for rn, cells in sorted(rows.items()):
            if rn <= header_rn:
                continue
            ts = month_to_utc(cells.get("A", ""))
            if not ts:
                continue
            for col, name in cols.items():
                val = cells.get(col, "")
                if val in ("", "..", "..."):
                    continue
                try:
                    fv = float(val)
                except Exception:
                    continue
                if not WANTED.search(name):
                    continue
                ev = {
                    "stream_id": "px.wb.pinksheet",
                    "nat_key": f"wb.pinksheet|{name}|{ts[:7]}",
                    "ts_utc": ts,
                    "ts_event_utc": ts,
                    "ts_reported_utc": now,
                    "ts_ingested_utc": now,
                    "value": fv,
                    "unit": name,
                    "title": name,
                    "url": SOURCE_URL,
                    "place": LANDING,
                    "attrib": ATTRIB,
                }
                fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
                n += 1
                if re.search(r"urea|dap|tsp|phosphate|potash|potassium|fertil", name, re.I):
                    fert += 1
    print(json.dumps({
        "stream": "px.wb.pinksheet", "rows": n, "fertilizer_rows": fert,
        "series_cols": len(cols), "file": str(out), "license": "CC BY 4.0",
        "attribution": ATTRIB, "source": SOURCE_URL,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
