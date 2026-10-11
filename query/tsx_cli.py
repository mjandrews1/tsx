#!/usr/bin/env python3
"""tsx CLI — thin SQL help for v0 (print canned queries)."""
import sys
Q = {
  "last": "SELECT * FROM v_eq_last;",
  "hourly": "SELECT * FROM v_eq_hourly ORDER BY hour_utc DESC LIMIT 24;",
  "count": "SELECT COUNT(*) FROM observation;",
  "caps": "bash tools/cap_check.sh",
}
def main():
    if len(sys.argv) < 2 or sys.argv[1] not in Q:
        print("tsx last|hourly|count|caps", file=sys.stderr)
        return 2
    print(Q[sys.argv[1]])
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
