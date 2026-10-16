#!/usr/bin/env python3
"""tsx#23 — archive stream list + load dedup (offline)."""
from __future__ import annotations

import ast
import os
import re
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    src = open(os.path.join(root, "tools", "archive_cdb2.py")).read()
    assert "STREAMS" in src, "archive_cdb2 must declare STREAMS"
    assert "wx.noaa.meta" not in src.split("STREAMS")[1].split(")")[0], (
        "meta must not be archived"
    )
    for s in ("eq.usgs", "wx.noaa", "wx.noaa.alerts"):
        assert s in src, s
    load = open(os.path.join(root, "load", "load_cdb2.py")).read()
    assert "tsx_nat_index" in load, "dedup via tsx_nat_index"
    assert "skipped" in load
    print("TEST archive_streams OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
