#!/bin/bash
# D3: NOAA alerts retention (sev >= 2).
# Filters staged alerts to minor+ severity, then loads.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
DB=${TSX_DB:-testdb}
LOG=/home/mark/tsx/load.log
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"

# Filter staged alerts to sev >= 2
/usr/bin/python3 acquire/alerts_retention.py --min-sev 2

# Load filtered alerts
/bin/bash load/load_stream.sh "$TSX_STAGE/wx.noaa.alerts.jsonl" wx.noaa.alerts
