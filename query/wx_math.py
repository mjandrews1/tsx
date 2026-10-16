"""Pure math for wx CLI (tsx#16) — importable for tests, no network."""
from __future__ import annotations

import math


def feels_like(t_c, wind_mps=None, rh=None):
    """Return (feels_c, formula) using NWS heat index / wind chill."""
    if t_c is None:
        return None, "none"
    t = float(t_c)
    if t >= 27 and rh is not None and float(rh) >= 40:
        tf = t * 9 / 5 + 32
        hi_f = (
            -42.379 + 2.04901523 * tf + 10.14333127 * rh
            - 0.22475541 * tf * rh - 0.00683783 * tf * tf
            - 0.05481717 * rh * rh + 0.00122874 * tf * tf * rh
            + 0.00085282 * tf * rh * rh
            - 0.00000199 * tf * tf * rh * rh
        )
        return (hi_f - 32) * 5 / 9, "heat_index"
    if t <= 10 and wind_mps is not None and float(wind_mps) >= 4.8:
        v = float(wind_mps) * 3.6
        wc = 13.12 + 0.6215 * t - 11.37 * (v ** 0.16) + 0.3965 * t * (v ** 0.16)
        return wc, "wind_chill"
    return t, "ambient"


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))
