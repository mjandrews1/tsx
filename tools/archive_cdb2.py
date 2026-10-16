#!/usr/bin/env python3
"""Archive old tsx rows to coldstore and delete from active Comdb2.

Usage:
  archive_cdb2.py [db] [days] [archive_dir]
Defaults: testdb, 90, $HOME/coldstore/tsx

Exports rows with ts_utc older than (now - days), then deletes those ids.
Respects coldstore cap via tools/cap_check.sh (tsx#4: cdb2sql on cron PATH).
"""
import csv, gzip, os, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# cron has no /opt/bb/bin — load scripts already export this (tsx#4)
_CDB2 = "/opt/bb/bin/cdb2sql"
if os.path.isdir("/opt/bb/bin"):
    os.environ["PATH"] = "/opt/bb/bin:" + os.environ.get("PATH", "")

DB = sys.argv[1] if len(sys.argv) > 1 else "testdb"
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 90
ARCH = Path(sys.argv[3] if len(sys.argv) > 3 else (Path.home() / "coldstore" / "tsx"))
# Archive every growing stream; skip timeless meta (tsx#19)
STREAMS = (
    "eq.usgs",
    "wx.noaa",
    "wx.noaa.alerts",
    "news.bbc",
    "px.wb.pinksheet",
)


def q(sql):
    bin_path = _CDB2 if os.path.isfile(_CDB2) else "cdb2sql"
    return subprocess.run([bin_path, DB, "local", sql], capture_output=True, text=True)


def archive_one(stream: str, cutoff: str, stamp: str, days: int) -> int:
    out = ARCH / f"{stream}.{stamp}.csv.gz"
    r = q(
        "SELECT id, stream_id, series_id, ts_utc, nat_key, value, unit, payload_json "
        f"FROM tsx_observation WHERE stream_id = \"{stream}\" AND ts_utc < \"{cutoff}\""
    )
    if r.returncode != 0:
        print(f"archive query failed stream={stream} rc={r.returncode}")
        return 0
    lines = (r.stdout or "").strip().splitlines()
    n = 0
    with gzip.open(out, "wt", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "stream_id", "series_id", "ts_utc", "nat_key", "value", "unit", "payload_json"])
        for line in lines:
            if "id=" not in line:
                continue
            w.writerow([line])
            n += 1
    if n:
        d = q(f"DELETE FROM tsx_observation WHERE stream_id = \"{stream}\" AND ts_utc < \"{cutoff}\"")
        print(f"archived={n} stream={stream} file={out.name} delete_rc={d.returncode}")
    else:
        print(f"archived=0 stream={stream} cutoff={cutoff}")
    return n


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = 0
    for stream in STREAMS:
        total += archive_one(stream, cutoff, stamp, DAYS)
    print(f"ARCHIVE ALL total={total} cutoff={cutoff} days={DAYS}")
    os.system(
        f"ARCHIVE_DIR={ARCH} ACTIVE_DIR=/home/mark/db ACTIVE_CAP_GB=2 ARCHIVE_CAP_GB=20 "
        "bash /home/mark/tsx/tools/cap_check.sh"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
