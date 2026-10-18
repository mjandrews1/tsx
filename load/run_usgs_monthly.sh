#!/bin/bash
# D2: USGS all_month + historical CSV backfill.
# Acquires all_month feed; historical CSV is loaded separately.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
DB=${TSX_DB:-testdb}
LOG=/home/mark/tsx/load.log
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"

# Acquire all_month (monthly earthquake feed)
/usr/bin/python3 acquire/usgs_quakes.py all_month

# Load into Comdb2
/bin/bash load/load_stream.sh "$TSX_STAGE/eq.usgs.all_month.jsonl" eq.usgs
