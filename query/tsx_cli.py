#!/usr/bin/env python3
"""tsx CLI — query Comdb2 views (tsx#3).

Usage:
  tsx_cli.py last [stream]
  tsx_cli.py stats
  tsx_cli.py hourly [stream]
  tsx_cli.py wx [station]\n  tsx_cli.py wxhourly [station]\n  tsx_cli.py alerts [area]\n  tsx_cli.py count
  tsx_cli.py sql "SELECT ..."
  tsx_cli.py caps
"""
from __future__ import annotations

import os
import subprocess
import sys

CDB2 = "/opt/bb/bin/cdb2sql"
DB = os.environ.get("TSX_DB", "testdb")


def run_sql(sql: str) -> int:
    bin_path = CDB2 if os.path.isfile(CDB2) else "cdb2sql"
    r = subprocess.run([bin_path, DB, "local", sql], capture_output=True, text=True)
    if r.stdout:
        print(r.stdout, end="" if r.stdout.endswith("\n") else "\n")
    if r.stderr:
        print(r.stderr, file=sys.stderr, end="")
    return r.returncode


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    cmd = argv[0]
    if cmd == "last":
        stream = argv[1] if len(argv) > 1 else ""
        if stream == "eq":
            return run_sql("SELECT * FROM v_last_eq")
        if stream == "wx":
            return run_sql("SELECT * FROM v_last_wx")
        return run_sql("SELECT * FROM v_last")
    if cmd == "stats":
        return run_sql("SELECT * FROM v_stats")
    if cmd == "hourly":
        stream = argv[1] if len(argv) > 1 else "eq.usgs"
        return run_sql(
            f"SELECT * FROM v_stats_hourly WHERE stream_id='{stream}' "
            "ORDER BY hour_utc DESC LIMIT 24"
        )
    if cmd == "count":
        return run_sql("SELECT COUNT(*) FROM tsx_observation")
    if cmd == "sql" and len(argv) > 1:
        return run_sql(argv[1])
    if cmd == "wx":
        station = argv[1] if len(argv) > 1 else ""
        if station:
            return run_sql(
                "SELECT nat_key, ts_utc, value, unit FROM tsx_observation "
                f"WHERE stream_id='wx.noaa' AND nat_key LIKE 'noaa|{station}|%' "
                "ORDER BY ts_utc DESC LIMIT 5"
            )
        return run_sql("SELECT * FROM v_stats_wx")
    if cmd == "wxhourly":
        station = argv[1] if len(argv) > 1 else ""
        if station:
            return run_sql(
                "SELECT hour_utc, avg_c, avg_wind_mps, avg_hpa, n FROM v_hourly_wx "
                f"WHERE station='noaa|{station}' ORDER BY hour_utc DESC LIMIT 24"
            )
        return run_sql("SELECT * FROM v_hourly_wx ORDER BY hour_utc DESC LIMIT 30")
    if cmd == "alerts":
        area = argv[1] if len(argv) > 1 else ""
        if area:
            return run_sql(
                "SELECT ts_utc, value AS sev, substr(payload_json,1,100) AS info FROM tsx_observation "
                f"WHERE stream_id='wx.noaa.alerts' AND place LIKE '%{area}%' "
                "ORDER BY ts_utc DESC LIMIT 20"
            )
        return run_sql(
            "SELECT ts_utc, value AS sev, substr(payload_json,1,100) AS info "
            "FROM tsx_observation WHERE stream_id='wx.noaa.alerts' "
            "ORDER BY ts_utc DESC LIMIT 20"
        )
    if cmd == "caps":
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return subprocess.call(["bash", os.path.join(root, "tools", "cap_check.sh")])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
