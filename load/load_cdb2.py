#!/usr/bin/env python3
"""Bulk-load JSONL into Comdb2 tsx_observation + tsx_nat_index.

Uses cdb2sql batch file (semicolon-separated) to avoid 1 process/row.
Dedup: skip (stream_id, nat_key) already in tsx_nat_index (31-bit hash PK).

Fixes (2026-10-17):
  - INSERT OR REPLACE on tsx_nat_index (hash collisions are expected at scale)
  - --single-transaction for atomic batches (no partial commits)
  - flock to prevent concurrent runs (race condition on have-set)
  - Accurate error counting
"""
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile

_CDB2 = "/opt/bb/bin/cdb2sql"
if os.path.isdir("/opt/bb/bin"):
    os.environ["PATH"] = "/opt/bb/bin:" + os.environ.get("PATH", "")
from pathlib import Path

DB = sys.argv[1] if len(sys.argv) > 1 else "testdb"
SRC = Path(sys.argv[2] if len(sys.argv) > 2 else "eq.usgs.all_day.jsonl")
DEFAULT_STREAM = sys.argv[3] if len(sys.argv) > 3 else "eq.usgs"
BATCH = 200
LOCKFILE = "/tmp/tsx_load_cdb2.lock"


def q(sql: str):
    return subprocess.run([_CDB2, DB, "local", sql], capture_output=True, text=True)


def run_file(path: Path):
    return subprocess.run(
        [_CDB2, DB, "local", "-f", str(path), "-s", "--single-transaction"],
        capture_output=True,
        text=True,
    )


def key_id(stream: str, nat: str) -> int:
    h = hashlib.sha256(f"{stream}|{nat}".encode()).hexdigest()
    return (int(h[:8], 16) % 2147483646) + 1


def esc(s: str) -> str:
    return (s or "").replace("'", "\'\'")


def main() -> int:
    # flock: prevent concurrent runs (race condition on have-set)
    lock_fd = open(LOCKFILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another load_cdb2.py is running; skipping", file=sys.stderr)
        return 0

    q("CREATE TABLE tsx_nat_index (id INTEGER PRIMARY KEY, stream_id TEXT, nat_key TEXT, obs_id INTEGER)")
    r = q("SELECT coalesce(max(id),0) FROM tsx_observation")
    try:
        nid = int((r.stdout or "0").strip().split("=")[-1].rstrip(")").strip() or "0") + 1
    except Exception:
        nid = 1

    have = set()
    rr = q("SELECT id FROM tsx_nat_index")
    for line in (rr.stdout or "").splitlines():
        if "id=" in line:
            try:
                have.add(int(line.split("id=")[1].split(")")[0].split(",")[0].strip()))
            except Exception:
                pass

    ok = skipped = err = 0
    buf = []
    nbuf = 0

    def flush():
        nonlocal nbuf, err
        if not buf:
            return
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
            fh.write(";\n".join(buf) + ";\n")
            path = Path(fh.name)
        p = run_file(path)
        path.unlink(missing_ok=True)
        if p.returncode != 0:
            err += nbuf
            print((p.stderr or p.stdout)[:500], file=sys.stderr)
        nbuf = 0
        buf.clear()

    for line in SRC.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        stream = o.get("stream_id") or DEFAULT_STREAM
        nat = o.get("nat_key") or o.get("url") or ""
        if not nat:
            err += 1
            continue
        hid = key_id(stream, nat)
        if hid in have:
            skipped += 1
            continue
        payload = json.dumps(
            {
                k: o.get(k)
                for k in (
                    "place", "lat", "lon", "depth_km", "title", "url",
                    "attrib", "ts_event_utc", "ts_reported_utc", "ts_ingested_utc",
                )
            },
            separators=(",", ":"),
        )[:2000]
        val = "NULL" if o.get("value") is None else str(float(o["value"]))
        ts = esc(o.get("ts_utc") or "")
        unit = esc(o.get("unit") or "")[:40]
        buf.append(
            f"INSERT INTO tsx_observation(id, stream_id, series_id, ts_utc, nat_key, value, unit, payload_json) "
            f"VALUES ({nid}, '{esc(stream)}', 0, '{ts}', '{esc(nat)[:200]}', {val}, '{unit}', '{esc(payload)}')"
        )
        # INSERT OR REPLACE: 32-bit hash collisions are expected at scale
        buf.append(
            f"INSERT OR REPLACE INTO tsx_nat_index(id, stream_id, nat_key, obs_id) VALUES ({hid}, '{esc(stream)}', '{esc(nat)[:200]}', {nid})"
        )
        have.add(hid)
        ok += 1
        nid += 1
        nbuf += 2
        if nbuf >= BATCH:
            flush()
    flush()
    print(f"loaded_ok={ok} skipped={skipped} err={err} next_id={nid}")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
