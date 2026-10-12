#!/usr/bin/env python3
"""tsx smoke tests: natural-key lookup, dedup, time-bucket correlation.

Usage:
  python3 tests/test_nattkey_dedup_bucket.py [db]
  Default db: testdb (U01 Comdb2)

Assumes sample rows from the seed (obs 90001–90005 / hash for us7000test1).
Creates its own rows with ids in 91000+ so it is repeatable.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys

DB = sys.argv[1] if len(sys.argv) > 1 else "testdb"
FAILED = 0


def q(sql: str):
    return subprocess.run(["cdb2sql", DB, "local", sql], capture_output=True, text=True)


def hid(stream: str, nat: str) -> int:
    h = hashlib.sha256(f"{stream}|{nat}".encode()).hexdigest()
    return (int(h[:8], 16) % 2147483646) + 1


def check(name: str, ok: bool, detail: str = ""):
    global FAILED
    status = "PASS" if ok else "FAIL"
    if not ok:
        FAILED += 1
    print(f"  [{status}] {name}  {detail}")


def main() -> int:
    print(f"tsx tests on Comdb2 db={DB}")

    # --- seed (idempotent-ish: high ids) ---
    print("\n== seed ==")
    q("CREATE TABLE tsx_observation (id INTEGER PRIMARY KEY, stream_id TEXT, series_id INTEGER, ts_utc TEXT, ingested_at TEXT, nat_key TEXT, value REAL, unit TEXT, payload_json TEXT)")
    q("CREATE TABLE tsx_nat_index (id INTEGER PRIMARY KEY, stream_id TEXT, nat_key TEXT, obs_id INTEGER)")
    q("CREATE TABLE tsx_timebucket (id INTEGER PRIMARY KEY, bucket_utc TEXT, stream_id TEXT, nat_key TEXT, ts_utc TEXT, value REAL)")

    obs = [
        (91001, "eq.usgs", "test-nk-1", "2026-10-11T21:11:00+00:00", 4.8, "mb", "2026-10-11T21"),
        (91002, "news.bbc", "https://bbc.example/test-nk", "2026-10-11T21:44:00+00:00", None, "headline", "2026-10-11T21"),
        (91003, "px.wb.pinksheet", "wb.pinksheet|Urea|2026-10-TEST", "2026-10-01T00:00:00+00:00", 407.5, "Urea", "2026-10-01T00"),
    ]
    for oid, sid, nat, ts, val, unit, bucket in obs:
        v = "NULL" if val is None else str(val)
        r = q(
            f"INSERT INTO tsx_observation(id, stream_id, series_id, ts_utc, ingested_at, nat_key, value, unit, payload_json) "
            f"VALUES ({oid}, '{sid}', 0, '{ts}', '2026-10-11T22:00:00+00:00', '{nat}', {v}, '{unit}', 'test')"
        )
        h = hid(sid, nat)
        q(f"INSERT INTO tsx_nat_index(id, stream_id, nat_key, obs_id) VALUES ({h}, '{sid}', '{nat}', {oid})")
        q(
            f"INSERT INTO tsx_timebucket(id, bucket_utc, stream_id, nat_key, ts_utc, value) "
            f"VALUES ({oid}, '{bucket}', '{sid}', '{nat}', '{ts}', {v})"
        )
        check(f"seed obs {oid}", r.returncode == 0, nat)

    # --- 1) natural-key lookup ---
    print("\n== 1) natural key lookup ==")
    for oid, sid, nat, ts, val, unit, bucket in obs:
        h = hid(sid, nat)
        r = q(f"SELECT obs_id FROM tsx_nat_index WHERE id={h}")
        out = r.stdout or ""
        check(
            f"hash {sid}|{nat} -> obs_id",
            f"obs_id={oid}" in out,
            f"hash={h} got={out.strip()[:60]}",
        )
        r2 = q(f"SELECT value FROM tsx_observation WHERE id={oid}")
        want = "NULL" if val is None else f"{float(val):.6f}"
        ok = want in (r2.stdout or "") or (val is not None and str(val) in (r2.stdout or ""))
        check(f"obs {oid} value", ok, (r2.stdout or "").strip()[:50])

    # --- 2) dedup: same nat_key cannot be inserted twice in nat_index ---
    print("\n== 2) dedup (PRIMARY KEY on hash) ==")
    h = hid("eq.usgs", "test-nk-1")
    r = q(f"INSERT INTO tsx_nat_index(id, stream_id, nat_key, obs_id) VALUES ({h}, 'eq.usgs', 'test-nk-1', 91001)")
    check(
        "duplicate nat_key insert rejected",
        r.returncode != 0,
        f"rc={r.returncode} {(r.stderr or '').strip()[:60]}",
    )
    # same observation natural key in observation table is not PK-constrained
    # (only id is); loader must use nat_index as the uniqueness gate
    r = q(f"SELECT count(*) FROM tsx_nat_index WHERE stream_id='eq.usgs' AND nat_key='test-nk-1'")
    check(
        "exactly one nat_index row for key",
        "count(*)=1" in (r.stdout or "").replace(" ", ""),
        (r.stdout or "").strip(),
    )

    # --- 3) time-bucket correlation ---
    print("\n== 3) time bucketing ==")
    r = q("SELECT stream_id, nat_key FROM tsx_timebucket WHERE bucket_utc='2026-10-11T21'")
    out = r.stdout or ""
    check("bucket has 2 streams in T21", "eq.usgs" in out and "news.bbc" in out, out.replace("\n", " ")[:80])

    r = q("SELECT stream_id, count(*) FROM tsx_timebucket WHERE bucket_utc='2026-10-11T21' GROUP BY stream_id")
    check("group by stream in bucket", "eq.usgs" in (r.stdout or "") and "news.bbc" in (r.stdout or ""))

    r = q(
        "SELECT t.nat_key, o.value FROM tsx_timebucket t "
        "JOIN tsx_observation o ON o.nat_key = t.nat_key "
        "WHERE t.bucket_utc='2026-10-11T21' AND t.stream_id='eq.usgs'"
    )
    check("join bucket -> observation", "test-nk-1" in (r.stdout or "") and "4.8" in (r.stdout or ""), (r.stdout or "").replace("\n", " ")[:80])

    # adjacent-hour correlation
    r = q(
        "SELECT bucket_utc FROM tsx_timebucket "
        "WHERE bucket_utc >= '2026-10-11T21' AND bucket_utc <= '2026-10-11T22' "
        "GROUP BY bucket_utc"
    )
    check("hour range scan", "2026-10-11T21" in (r.stdout or ""), (r.stdout or "").replace("\n", " ")[:80])

    print(f"\n{'ALL PASS' if FAILED == 0 else f'FAILED {FAILED}'}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
