#!/bin/bash
# B2: FRED macro series (CPI, UNRATE, DFF, GDP, DGS10).
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"
/usr/bin/python3 acquire/fred_macro.py
/bin/bash load/load_stream.sh "$TSX_STAGE/macro.fred.jsonl" macro.fred
