#!/usr/bin/env python3
"""Load JSONL event rows into Comdb2 observation (idempotent on nat_key)."""
from __future__ import annotations
import json, os, sys
from pathlib import Path

def rows(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line=line.strip()
            if not line:
                continue
            o=json.loads(line)
            yield (
                o.get("ts_utc"), o.get("nat_key"), o.get("value"),
                o.get("unit") or "mww", o.get("series_id") or 0,
                json.dumps({k:o.get(k) for k in ("place","lat","lon","depth_km","title","url")}, separators=(",",":"))[:7900],
            )

def main() -> int:
    if len(sys.argv) < 2:
        print("usage: load_obs.py <file.jsonl> [stream_id]", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    stream = sys.argv[2] if len(sys.argv) > 2 else "eq.usgs"
    # Print SQL statements for csql2 (no driver assumed in v0)
    for ts, nat, val, unit, sid, payload in rows(path):
        val_s = "NULL" if val is None else str(float(val))
        payload_s = payload.replace("'", "''")
        print(
            f"INSERT INTO observation(stream_id, series_id, ts_utc, nat_key, value, unit, payload_json) "
            f"VALUES('{stream}', {int(sid)}, '{ts}', '{nat}', {val_s}, '{unit}', '{payload_s}') "
            f"ON CONFLICT (stream_id, nat_key) DO UPDATE SET value=excluded.value, payload_json=excluded.payload_json;"
        )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
