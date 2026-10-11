#!/usr/bin/env python3
"""Load staged JSONL into Comdb2 tsx_observation via cdb2sql.

Dedup: skip rows whose (stream_id, nat_key) already exists.
"""
import json, subprocess, sys
from pathlib import Path

DB = sys.argv[1] if len(sys.argv) > 1 else "testdb"
SRC = Path(sys.argv[2] if len(sys.argv) > 2 else "eq.usgs.all_day.jsonl")
STREAM = "eq.usgs"

def q(sql: str):
    return subprocess.run(["cdb2sql", DB, "local", sql], capture_output=True, text=True)

def main() -> int:
    r = q("SELECT coalesce(max(id),0) FROM tsx_observation")
    try:
        nid = int((r.stdout or "0").strip().split("=")[-1].rstrip(")").strip() or "0") + 1
    except Exception:
        nid = 1
    ok = skipped = err = 0
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        nat = (o.get("nat_key") or "").replace("'", "''")
        chk = q(f"SELECT id FROM tsx_observation WHERE stream_id='{STREAM}' AND nat_key='{nat}'")
        if chk.returncode == 0 and "id=" in (chk.stdout or ""):
            skipped += 1
            continue
        payload = json.dumps(
            {k: o.get(k) for k in ("place", "lat", "lon", "depth_km", "title", "url")},
            separators=(",", ":"),
        )[:200].replace("'", "''")
        val = "NULL" if o.get("value") is None else str(float(o["value"]))
        ts = (o.get("ts_utc") or "").replace("'", "''")
        unit = (o.get("unit") or "ml").replace("'", "''")
        sql = (
            f"INSERT INTO tsx_observation(id, stream_id, series_id, ts_utc, nat_key, value, unit, payload_json) "
            f"VALUES ({nid}, '{STREAM}', 0, '{ts}', '{nat}', {val}, '{unit}', '{payload}')"
        )
        if q(sql).returncode == 0:
            ok += 1
            nid += 1
        else:
            err += 1
    print(f"loaded_ok={ok} skipped={skipped} err={err} next_id={nid}")
    return 0 if err == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
