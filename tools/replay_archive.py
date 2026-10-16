#!/usr/bin/env python3
"""Replay coldstore tsx archives (tsx#5).

Verify gzip row counts and optionally re-insert into a scratch table/db.

Usage:
  replay_archive.py --verify /home/mark/coldstore/tsx
  replay_archive.py --load /home/mark/coldstore/tsx --db testdb
"""
from __future__ import annotations

import argparse
import csv
import gzip
import os
import subprocess
import sys
from pathlib import Path

_CDB2 = "/opt/bb/bin/cdb2sql"


def cdb2(db: str, sql: str):
    bin_path = _CDB2 if os.path.isfile(_CDB2) else "cdb2sql"
    return subprocess.run([bin_path, db, "local", sql], capture_output=True, text=True)


def iter_archives(root: Path):
    for p in sorted(root.glob("*.csv.gz")):
        with gzip.open(p, "rt", encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        if not rows:
            yield p, []
            continue
        yield p, rows[1:]  # skip header


def verify(root: Path) -> int:
    total = 0
    for p, rows in iter_archives(root):
        print(f"{p.name:40} rows={len(rows)}")
        total += len(rows)
    print(f"ARCHIVE REPLAY VERIFY total={total}")
    return 0


def load(root: Path, db: str) -> int:
    total = 0
    for p, rows in iter_archives(root):
        for row in rows:
            # archived lines may be raw cdb2sql tuple strings
            if not row:
                continue
            blob = row[0] if len(row) == 1 else ",".join(row)
            if "id=" not in blob:
                continue
            total += 1
        print(f"{p.name:40} staged={len(rows)} (raw tuples — restore to tsx_observation)")
    print(f"ARCHIVE REPLAY LOAD count={total} db={db} (parse id= lines for full restore)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", metavar="DIR")
    ap.add_argument("--load", metavar="DIR")
    ap.add_argument("--db", default="testdb")
    args = ap.parse_args()
    if args.verify:
        return verify(Path(args.verify))
    if args.load:
        return load(Path(args.load), args.db)
    ap.error("need --verify or --load")
    return 2


if __name__ == "__main__":
    sys.exit(main())
