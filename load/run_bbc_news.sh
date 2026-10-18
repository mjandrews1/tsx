#!/bin/bash
# D5: BBC News RSS — 1-year text-only window.
# Acquires BBC News RSS and loads text-only articles.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
DB=${TSX_DB:-testdb}
LOG=/home/mark/tsx/load.log
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"

# Acquire BBC News RSS (world category)
/usr/bin/python3 acquire/bbc_news.py --category world

# Load into Comdb2
/bin/bash load/load_stream.sh "$TSX_STAGE/news.bbc.jsonl" news.bbc
