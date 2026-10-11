#!/usr/bin/env python3
"""Load JSONL into Comdb2 with nat_key dedup via tsx_nat_index (31-bit hash PK).

Comdb2 on this cluster rejects CREATE INDEX / UNIQUE / composite PK
(dyns_load_schema_string). Workaround:
  tsx_nat_index(id=hash31(stream_id,nat_key), stream_id, nat_key, obs_id)
"""
import hashlib, json, subprocess, sys
from pathlib import Path

DB = sys.argv[1] if len(sys.argv) > 1 else "testdb"
SRC = Path(sys.argv[2] if len(sys.argv) > 2 else "eq.usgs.all_day.jsonl")
STREAM = "eq.usgs"

def q(sql: str):
    return subprocess.run(["cdb2sql", DB, "local", sql], capture_output=True, text=True)

def key_id(stream: str, nat: str) -> int:
    h = hashlib.sha256(f"{stream}|{nat}".encode()).hexdigest()
    return (int(h[:8], 16) % 2147483646) + 1

def exists(hid: int) -> bool:
    r = q(f"SELECT id FROM tsx_nat_index WHERE id={hid}")
    return "id=" in (r.stdout or "")

def main() -> int:
    # ensure key table
    q("CREATE TABLE tsx_nat_index (id INTEGER PRIMARY KEY, stream_id TEXT, nat_key TEXT, obs_id INTEGER)")
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
        hid = key_id(STREAM, nat)
        if exists(hid):
            skipped += 1
            continue
        payload = json.dumps(
            {k: o.get(k) for k in ("place", "lat", "lon", "depth_km", "title", "url")},
            separators=(",", ":"),
        )[:200].replace("'", "''")
        val = "NULL" if o.get("value") is None else str(float(o["value"]))
        ts = (o.get("ts_utc") or "").replace("'", "''")
        unit = (o.get("unit") or "ml").replace("'", "''")
        ins = (
            f"INSERT INTO tsx_observation(id, stream_id, series_id, ts_utc, nat_key, value, unit, payload_json) "
            f"VALUES ({nid}, '{STREAM}', 0, '{ts}', '{nat}', {val}, '{unit}', '{payload}')"
        )
        if q(ins).returncode == 0:
            q(f"INSERT INTO tsx_nat_index(id, stream_id, nat_key, obs_id) VALUES ({hid}, '{STREAM}', '{nat}', {nid})")
            ok += 1
            nid += 1
        else:
            err += 1
    print(f"loaded_ok={ok} skipped={skipped} err={err} next_id={nid}")
    return 0 if err == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
