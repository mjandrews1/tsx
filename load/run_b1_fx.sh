#!/bin/bash
# B1: ECB daily FX reference rates.
set -euo pipefail
export PATH=/opt/bb/bin:/usr/bin:/bin
export TSX_STAGE=${TSX_STAGE:-/home/mark/tsx-staging}
cd /home/mark/tsx
mkdir -p "$TSX_STAGE"
/usr/bin/python3 acquire/ecb_fx.py
/bin/bash load/load_stream.sh "$TSX_STAGE/fx.ecb.jsonl" fx.ecb
