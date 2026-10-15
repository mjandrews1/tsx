#!/bin/bash
# Load staged USGS quakes into Comdb2 (idempotent via tsx_nat_index).
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
DB=${TSX_DB:-testdb}
SRC=${TSX_STAGE:-/home/mark/tsx-staging}/eq.usgs.all_day.jsonl
LOG=/home/mark/tsx/load.log
cd /home/mark/tsx
if [ ! -s "$SRC" ]; then
  echo "{\"at\":\"$(date -u +%FT%TZ)\",\"status\":\"empty\",\"src\":\"$SRC\"}" >> "$LOG"
  exit 0
fi
/usr/bin/python3 /home/mark/tsx/load/load_cdb2.py "$DB" "$SRC" eq.usgs
echo "{\"at\":\"$(date -u +%FT%TZ)\",\"status\":\"done\",\"src\":\"$SRC\"}" >> "$LOG"
