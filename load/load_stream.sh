#!/bin/bash
# load_stream.sh <jsonl> <stream_id> [logfile]
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
SRC=${1:?jsonl}
STREAM=${2:?stream_id}
LOG=${3:-/home/mark/tsx/load.log}
if [ ! -s "$SRC" ]; then
  echo "{\"at\":\"$(date -u +%FT%TZ)\",\"status\":\"empty\",\"src\":\"$SRC\",\"stream\":\"$STREAM\"}" >> "$LOG"
  exit 0
fi
/usr/bin/python3 /home/mark/tsx/load/load_cdb2.py "${TSX_DB:-testdb}" "$SRC" "$STREAM"
echo "{\"at\":\"$(date -u +%FT%TZ)\",\"status\":\"done\",\"src\":\"$SRC\",\"stream\":\"$STREAM\"}" >> "$LOG"
