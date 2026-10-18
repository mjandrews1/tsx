#!/bin/bash
# D4: Pinksheet full monthly history backfill.
# Loads World Bank Commodity Markets (Pink Sheet) monthly prices.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
DB=${TSX_DB:-testdb}
LOG=/home/mark/tsx/load.log
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"

# Acquire + stage pinksheet data
/usr/bin/python3 acquire/worldbank_pinksheet.py

# Load into Comdb2
/bin/bash load/load_stream.sh "$TSX_STAGE/wb.pinksheet.jsonl" px.wb.pinksheet
