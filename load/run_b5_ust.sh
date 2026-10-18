#!/bin/bash
# B5: US Treasury yield curve daily.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"
/usr/bin/python3 acquire/ust_yield.py
/bin/bash load/load_stream.sh "$TSX_STAGE/rates.ust.jsonl" rates.ust
