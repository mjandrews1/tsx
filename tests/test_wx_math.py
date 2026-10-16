#!/usr/bin/env python3
"""tsx#16 offline tests for haversine + feels_like."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "query"))

from wx_math import feels_like, haversine_km  # noqa: E402


def main() -> int:
    d = haversine_km(40.779, -73.88, 40.779, -73.88)
    assert abs(d) < 1e-6, d
    d2 = haversine_km(40.779, -73.88, 42.361, -71.011)
    assert 280 < d2 < 310, d2  # KLGA-BOS ~296 km
    f, how = feels_like(29, 16.7, 85)
    assert how == "heat_index" and f > 29, (f, how)
    f, how = feels_like(1, 12.96, 59)
    assert how == "wind_chill" and f < 1, (f, how)
    f, how = feels_like(25, 18, 94)
    assert how == "ambient" and abs(f - 25) < 1e-6
    print("TEST wx_math OK", round(haversine_km(40.779, -73.88, 42.361, -71.011), 1), "km KLGA-BOS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
