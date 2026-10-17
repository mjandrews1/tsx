#!/bin/bash
# load_stream.sh <jsonl> <stream_id> [logfile]
# Bulk load via multi-row INSERT (fast_load.py). Idempotent via tsx_nat_index.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
SRC=${1:?jsonl}
STREAM=${2:?stream_id}
LOG=${3:-/home/mark/tsx/load.log}
if [ ! -s "$SRC" ]; then
  echo "{\"at\":\"$(date -u +%FT%TZ)\",\"status\":\"empty\",\"src\":\"$SRC\",\"stream\":\"$STREAM\"}" >> "$LOG"
  exit 0
fi
/usr/bin/python3 /home/mark/tsx/load/fast_load.py "${TSX_DB:-testdb}" "$SRC" "$STREAM" >> "$LOG" 2>&1
