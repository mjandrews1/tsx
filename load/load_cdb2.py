#!/usr/bin/env python3
"""Load staged JSONL into Comdb2 tsx_observation via cdb2sql."""
import json, subprocess, sys
from pathlib import Path

DB = sys.argv[1] if len(sys.argv) > 1 else "testdb"
SRC = Path(sys.argv[2] if len(sys.argv) > 2 else "eq.usgs.all_day.jsonl")
STREAM = "eq.usgs"

def run_sql(sql: str) -> int:
    p = subprocess.run(["cdb2sql", DB, "local", sql], capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr[-300:] + "\n")
    return p.returncode

def main() -> int:
    # next id
    r = subprocess.run(["cdb2sql", DB, "local", "SELECT coalesce(max(id),0)+1 FROM tsx_observation"],
                       capture_output=True, text=True)
    try:
        nid = int(r.stdout.strip().split("=")[-1].rstrip(")").strip() or "1")
    except Exception:
        nid = 1
    ok = err = 0
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        payload = json.dumps({k: o.get(k) for k in ("place","lat","lon","depth_km","title","url")}, separators=(",", ":"))[:200]
        payload = payload.replace("'", "''")
        val = "NULL" if o.get("value") is None else str(float(o["value"]))
        nat = (o.get("nat_key") or "").replace("'", "''")
        ts = o.get("ts_utc") or ""
        unit = (o.get("unit") or "ml").replace("'", "''")
        sql = (
            f"INSERT INTO tsx_observation(id, stream_id, series_id, ts_utc, nat_key, value, unit, payload_json) "
            f"VALUES ({nid}, '{STREAM}', 0, '{ts}', '{nat}', {val}, '{unit}', '{payload}')"
        )
        if run_sql(sql) == 0:
            ok += 1
            nid += 1
        else:
            err += 1
    print(f"loaded_ok={ok} err={err} next_id={nid}")
    return 0 if err == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
