#!/bin/bash
# Unified hourly wx job (tsx#14): obs + alerts; meta daily at hour 3.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"
/bin/bash load/run_noaa.sh
/bin/bash load/run_alerts.sh
if [ "$(date -u +%H)" = "03" ]; then
  /bin/bash load/run_stations_meta.sh || true
fi
echo "{"at":"$(date -u +%FT%TZ)","status":"wx_hourly_ok"}"
