#!/usr/bin/env python3
"""Archive old tsx rows to coldstore and delete from active Comdb2.

Usage:
  archive_cdb2.py [db] [days] [archive_dir]
Defaults: testdb, 90, $HOME/coldstore/tsx
"""
import csv, gzip, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

DB = sys.argv[1] if len(sys.argv) > 1 else "testdb"
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 90
ARCH = Path(sys.argv[3] if len(sys.argv) > 3 else (Path.home() / "coldstore" / "tsx"))
STREAM = "eq.usgs"

def q(sql):
    return subprocess.run(["cdb2sql", DB, "local", sql], capture_output=True, text=True)

def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # export all rows with date < cutoff - use string compare on ts_utc (ISO)
    out = ARCH / f"{STREAM}.{cutoff}.csv.gz"
    r = q(f"SELECT id, stream_id, series_id, ts_utc, nat_key, value, unit, payload_json FROM tsx_observation WHERE ts_utc < '{cutoff}'")
    lines = (r.stdout or "").strip().splitlines()
    n = 0
    with gzip.open(out, "wt", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "stream_id", "series_id", "ts_utc", "nat_key", "value", "unit", "payload_json"])
        for line in lines:
            # cdb2sql prints (id=.., ...) tuples — keep raw as id parse
            if "id=" not in line:
                continue
            w.writerow([line])
            n += 1
    # delete archived ids (simple: delete all rows older than cutoff)
    d = q(f"DELETE FROM tsx_observation WHERE ts_utc < '{cutoff}'")
    print(f"archived={n} file={out} delete_rc={d.returncode} cutoff={cutoff}")
    # cap check
    os.system(f"ARCHIVE_DIR={ARCH} ACTIVE_DIR=/home/mark/db ACTIVE_CAP_GB=2 ARCHIVE_CAP_GB=20 bash /home/mark/tsx/tools/cap_check.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
