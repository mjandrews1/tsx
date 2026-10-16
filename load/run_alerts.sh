#!/bin/bash
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
mkdir -p "$TSX_STAGE"
/usr/bin/python3 /home/mark/tsx/acquire/noaa_alerts.py
/home/mark/tsx/load/load_stream.sh "$TSX_STAGE/wx.noaa.alerts.jsonl" wx.noaa.alerts
