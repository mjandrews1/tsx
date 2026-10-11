#!/bin/bash
set -euo pipefail
ROOT="${TSX_ROOT:-$HOME/tsx}"
export TSX_STAGE="${TSX_STAGE:-$HOME/tsx-staging}"
mkdir -p "$TSX_STAGE"
python3 "$ROOT/acquire/usgs_quakes.py" all_day
# optional: pipe to csql2 via load_obs.py
