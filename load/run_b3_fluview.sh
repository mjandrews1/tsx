#!/bin/bash
# B3: CDC FluView ILI weekly.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"
/usr/bin/python3 acquire/cdc_fluview.py
/bin/bash load/load_stream.sh "$TSX_STAGE/health.fluview.jsonl" health.fluview
