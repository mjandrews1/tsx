#!/bin/bash
# run_data_jobs.sh — unified data acquisition runner.
# Runs all tsx feed acquires in sequence. Idempotent via tsx_nat_index dedup.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"

LOG=/home/mark/tsx/load.log
FAIL=0

run_job() {
    local name="$1"
    local cmd="$2"
    echo "$(date -u +%FT%TZ) [$name] start" >> "$LOG"
    if eval "$cmd" >> "$LOG" 2>&1; then
        echo "$(date -u +%FT%TZ) [$name] OK" >> "$LOG"
    else
        echo "$(date -u +%FT%TZ) [$name] FAIL" >> "$LOG"
        FAIL=1
    fi
}

# --- D-series (depth) ---
run_job "D1-wx-history"   "/bin/bash load/run_wx_history.sh"
run_job "D2-usgs-monthly" "/bin/bash load/run_usgs_monthly.sh"
run_job "D3-alerts-ret"   "/bin/bash load/run_alerts_retention.sh"
run_job "D5-bbc-news"     "/bin/bash load/run_bbc_news.sh"

# --- B-series (breadth) ---
run_job "B1-ecb-fx"       "/bin/bash load/run_b1_fx.sh"
run_job "B5-ust-yield"    "/bin/bash load/run_b5_ust.sh"

# --- hourly/standing (idempotent) ---
run_job "wx-hourly"        "/bin/bash load/run_wx_hourly.sh"
run_job "alerts"           "/bin/bash load/run_alerts.sh"
run_job "usgs-day"         "/bin/bash load/load_usgs.sh"

echo "$(date -u +%FT%TZ) [all-jobs] done fail=$FAIL" >> "$LOG"
exit $FAIL
