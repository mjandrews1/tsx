#!/usr/bin/env bash
# Apply tsx terminal views (tsx#3). Comdb2 needs one statement per call.
set -euo pipefail
DB="${1:-testdb}"
CDB2="${CDB2SQL:-/opt/bb/bin/cdb2sql}"
here="$(cd "$(dirname "$0")/.." && pwd)"
sql="$here/views/v_last.sql"
# split on blank-line-separated CREATE VIEW blocks into single lines
python3 - "$sql" <<'PY' | while IFS= read -r stmt; do
import sys
text = open(sys.argv[1]).read()
parts = text.split("CREATE VIEW ")
for p in parts[1:]:
    stmt = "CREATE VIEW " + " ".join(p.splitlines())
    stmt = stmt.split(";")[0].strip()
    if stmt:
        print(stmt)
PY
  echo "APPLY ${stmt:0:40}..."
  "$CDB2" "$DB" local "$stmt" >/dev/null
done
echo "APPLY VIEWS OK $DB"
