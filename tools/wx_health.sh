#!/usr/bin/env bash
# tsx#24 — one-shot wx/tsx ops health.
set -uo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
ok=0; fail=0
chk() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "OK   $name"; ok=$((ok+1))
  else
    echo "FAIL $name"; fail=$((fail+1))
  fi
}
echo "tsx health $(date -u +%Y-%m-%dT%H:%M:%SZ)"
chk "cdb2sql present" test -x /opt/bb/bin/cdb2sql
chk "cap_check" bash /home/mark/tsx/tools/cap_check.sh
chk "cron wx_hourly" sh -c "crontab -l | grep -q run_wx_hourly"
chk "cron alerts" sh -c "crontab -l | grep -q run_alerts"
chk "load log fresh" sh -c "test -n \"$(find /home/mark/tsx/load.log -mmin -150 2>/dev/null)\""
echo "--- streams ---"
/opt/bb/bin/cdb2sql testdb local "SELECT stream_id, COUNT(*) AS n FROM tsx_observation GROUP BY stream_id" 2>/dev/null || fail=$((fail+1))
echo "HEALTH ok=$ok fail=$fail"
test "$fail" -eq 0
