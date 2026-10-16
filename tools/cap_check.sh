#!/usr/bin/env bash
# cap_check.sh — verify tsx active DB and archive stay under caps.
set -euo pipefail
ACTIVE_CAP_GB="${ACTIVE_CAP_GB:-2}"
ARCHIVE_CAP_GB="${ARCHIVE_CAP_GB:-20}"
# Default archive path: U02 coldstore when run there
ARCHIVE_DIR="${ARCHIVE_DIR:-$HOME/coldstore/tsx}"
# Optional: Comdb2 db dir (when measuring "active")
# Default to Comdb2 db dir when present (U01/U02)
ACTIVE_DIR="${ACTIVE_DIR:-}"
if [ -z "$ACTIVE_DIR" ] && [ -d "$HOME/db" ]; then
  ACTIVE_DIR="$HOME/db"
fi

fail=0
echo "tsx cap check $(date -u +%Y-%m-%dT%H:%M:%SZ)"

gb_of() {
  # $1 path — print size in GB (float)
  if [ ! -e "$1" ]; then
    echo 0
    return
  fi
  local k
  k=$(du -sk "$1" 2>/dev/null | awk '{print $1}')
  awk -v k="$k" 'BEGIN{printf "%.3f", k/1024/1024}'
}

a=0
if [ -n "$ACTIVE_DIR" ]; then
  a=$(gb_of "$ACTIVE_DIR")
  echo "active  $ACTIVE_DIR  ${a} GB  (cap ${ACTIVE_CAP_GB})"
  awk -v a="$a" -v c="$ACTIVE_CAP_GB" 'BEGIN{exit !(a<=c)}' || { echo "FAIL active over cap"; fail=1; }
else
  echo "active  (set ACTIVE_DIR to measure Comdb2 db)"
fi

ar=$(gb_of "$ARCHIVE_DIR")
echo "archive $ARCHIVE_DIR  ${ar} GB  (cap ${ARCHIVE_CAP_GB})"
awk -v a="$ar" -v c="$ARCHIVE_CAP_GB" 'BEGIN{exit !(a<=c)}' || { echo "FAIL archive over cap"; fail=1; }

exit "$fail"
