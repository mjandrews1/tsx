#!/usr/bin/env bash
# tsx#1 P0 demo pipeline one-shot (schema assumed; cron does acquire/load/caps).
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH=/opt/bb/bin:/usr/bin:/bin
echo "=== cap ==="
bash tools/cap_check.sh
echo "=== streams ==="
python3 query/tsx_cli.py sql "SELECT stream_id, COUNT(*) AS n FROM tsx_observation GROUP BY stream_id"
echo "=== hourly eq.usgs ==="
python3 query/tsx_cli.py hourly eq.usgs
echo "=== last ==="
python3 query/tsx_cli.py last eq
echo "P0 DEMO OK"
