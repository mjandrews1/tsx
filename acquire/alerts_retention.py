#!/usr/bin/env python3
"""D3: NOAA alerts retention filter (severity >= 2 = minor and above).

Filters staged wx.noaa.alerts.jsonl to keep only alerts with sev_val >= min_sev.
Rewrites the staging file in place.

Usage:
  alerts_retention.py [--min-sev 2]
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    min_sev = 2
    if "--min-sev" in sys.argv:
        idx = sys.argv.index("--min-sev")
        if idx + 1 < len(sys.argv):
            min_sev = int(sys.argv[idx + 1])

    stage = Path(os.environ.get("TSX_STAGE") or (Path.home() / "tsx-staging"))
    src = stage / "wx.noaa.alerts.jsonl"
    if not src.is_file():
        print(json.dumps({"stream": "wx.noaa.alerts", "status": "empty", "at": datetime.now(timezone.utc).isoformat()}))
        return 0

    now = datetime.now(timezone.utc).isoformat()
    kept = 0
    dropped = 0
    tmp = src.with_suffix(".tmp")

    with src.open(encoding="utf-8") as f, tmp.open("w", encoding="utf-8") as out:
        for line in f:
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                dropped += 1
                continue
            sev = ev.get("value", 0)
            if isinstance(sev, (int, float)) and sev >= min_sev:
                out.write(line if line.endswith("\n") else line + "\n")
                kept += 1
            else:
                dropped += 1

    tmp.replace(src)
    print(json.dumps({
        "stream": "wx.noaa.alerts",
        "kept": kept,
        "dropped": dropped,
        "min_sev": min_sev,
        "at": now,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
