#!/bin/bash
# D1 history backfill loader: acquire IEM ASOS history + bulk load.
# Run on demand or from cron. Idempotent via tsx_nat_index dedup.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
DB=${TSX_DB:-testdb}
LOG=/home/mark/tsx/load.log
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"

# 1. acquire (writes wx.noaa.history.jsonl)
/usr/bin/python3 /home/mark/tsx/acquire/wx_history.py

# 2. bulk load (multi-row INSERT, single cdb2sql --chunk pass)
/usr/bin/python3 /home/mark/tsx/load/fast_load.py "$DB" "$TSX_STAGE/wx.noaa.history.jsonl" wx.noaa >> "$LOG" 2>&1
