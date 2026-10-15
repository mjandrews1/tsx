#!/bin/bash
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
mkdir -p "$TSX_STAGE"
/usr/bin/python3 /home/mark/tsx/acquire/noaa_obs.py
/home/mark/tsx/load/load_stream.sh "$TSX_STAGE/wx.noaa.obs.jsonl" wx.noaa
