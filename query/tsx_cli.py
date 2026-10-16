#!/usr/bin/env python3
"""tsx CLI — query Comdb2 views (tsx#3).

Usage:
  tsx_cli.py last [stream]
  tsx_cli.py stats
  tsx_cli.py hourly [stream]
  tsx_cli.py wx [station]\n  tsx_cli.py wxhourly [station]\n  tsx_cli.py alerts [area]\n  tsx_cli.py stations\n  tsx_cli.py wxday [station]\n  tsx_cli.py wxextremes [hours]\n  tsx_cli.py wxfeels [station]\n  tsx_cli.py wxnow\n  tsx_cli.py export <stream> [file]\n  tsx_cli.py export-all [dir]\n  tsx_cli.py near <lat> <lon>\n  tsx_cli.py compare ST1 ST2\n  tsx_cli.py alerts-near <lat> <lon> [km]\n  tsx_cli.py alerts [--severe] [area]\n  tsx_cli.py count
  tsx_cli.py sql "SELECT ..."
  tsx_cli.py caps
"""
from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wx_math import feels_like, haversine_km  # noqa: E402

CDB2 = "/opt/bb/bin/cdb2sql"
DB = os.environ.get("TSX_DB", "testdb")


def run_sql_capture(sql: str) -> str:
    bin_path = CDB2 if os.path.isfile(CDB2) else "cdb2sql"
    r = subprocess.run([bin_path, DB, "local", sql], capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


def run_sql(sql: str) -> int:
    bin_path = CDB2 if os.path.isfile(CDB2) else "cdb2sql"
    r = subprocess.run([bin_path, DB, "local", sql], capture_output=True, text=True)
    if r.stdout:
        print(r.stdout, end="" if r.stdout.endswith("\n") else "\n")
    if r.stderr:
        print(r.stderr, file=sys.stderr, end="")
    return r.returncode


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    cmd = argv[0]
    if cmd == "last":
        stream = argv[1] if len(argv) > 1 else ""
        if stream == "eq":
            return run_sql("SELECT * FROM v_last_eq")
        if stream == "wx":
            return run_sql("SELECT * FROM v_last_wx")
        return run_sql("SELECT * FROM v_last")
    if cmd == "stats":
        return run_sql("SELECT * FROM v_stats")
    if cmd == "hourly":
        stream = argv[1] if len(argv) > 1 else "eq.usgs"
        return run_sql(
            f"SELECT * FROM v_stats_hourly WHERE stream_id='{stream}' "
            "ORDER BY hour_utc DESC LIMIT 24"
        )
    if cmd == "count":
        return run_sql("SELECT COUNT(*) FROM tsx_observation")
    if cmd == "sql" and len(argv) > 1:
        return run_sql(argv[1])
    if cmd == "wx":
        station = argv[1] if len(argv) > 1 else ""
        if station:
            return run_sql(
                "SELECT nat_key, ts_utc, value, unit FROM tsx_observation "
                f"WHERE stream_id='wx.noaa' AND nat_key LIKE 'noaa|{station}|%' "
                "ORDER BY ts_utc DESC LIMIT 5"
            )
        return run_sql("SELECT * FROM v_stats_wx")
    if cmd == "wxhourly":
        station = argv[1] if len(argv) > 1 else ""
        if station:
            return run_sql(
                "SELECT hour_utc, avg_c, avg_wind_mps, avg_hpa, avg_rh, avg_dew_c, n FROM v_hourly_wx "
                f"WHERE station='noaa|{station}' ORDER BY hour_utc DESC LIMIT 24"
            )
        return run_sql("SELECT * FROM v_hourly_wx ORDER BY hour_utc DESC LIMIT 30")
    if cmd == "alerts":
        rest = argv[1:]
        severe = "--severe" in rest
        rest = [x for x in rest if x != "--severe"]
        area = rest[0] if rest else ""
        sev_sql = " AND value >= 4" if severe else ""
        if area:
            return run_sql(
                "SELECT ts_utc, value AS sev, substr(payload_json,1,100) AS info FROM tsx_observation "
                f"WHERE stream_id='wx.noaa.alerts' AND payload_json LIKE '%{area}%'"
                + sev_sql + " ORDER BY ts_utc DESC LIMIT 20"
            )
        return run_sql(
            "SELECT ts_utc, value AS sev, substr(payload_json,1,100) AS info "
            "FROM tsx_observation WHERE stream_id='wx.noaa.alerts'"
            + sev_sql + " ORDER BY ts_utc DESC LIMIT 20"
        )
    if cmd == "stations":
        return run_sql("SELECT * FROM v_stations")
    if cmd == "wxday":
        station = argv[1] if len(argv) > 1 else "KLGA"
        return run_sql(
            "SELECT substr(ts_utc,1,10) AS day, "
            "MIN(value) AS min_c, AVG(value) AS avg_c, MAX(value) AS max_c "
            "FROM tsx_observation WHERE stream_id='wx.noaa' "
            f"AND nat_key LIKE 'noaa|{station}|2%' "
            "GROUP BY substr(ts_utc,1,10) ORDER BY day DESC LIMIT 7"
        )
    if cmd == "wxextremes":
        from datetime import datetime, timedelta, timezone
        hours = argv[1] if len(argv) > 1 else "24"
        if not str(hours).isdigit():
            hours = "24"
        cut = (datetime.now(timezone.utc) - timedelta(hours=int(hours))).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        return run_sql(
            "SELECT substr(nat_key,1,9) AS station, "
            "MIN(CASE WHEN nat_key NOT LIKE '%|w|%' AND nat_key NOT LIKE '%|p|%' THEN value END) AS min_c, "
            "MAX(CASE WHEN nat_key NOT LIKE '%|w|%' AND nat_key NOT LIKE '%|p|%' THEN value END) AS max_c, "
            "MAX(CASE WHEN nat_key LIKE '%|w|%' THEN value END) AS max_wind_mps "
            "FROM tsx_observation WHERE stream_id='wx.noaa' "
            f"AND ts_utc >= '{cut}' "
            "GROUP BY substr(nat_key,1,9) ORDER BY station"
        )
    if cmd == "wxfeels":
        station = argv[1] if len(argv) > 1 else "KLGA"
        # last temp / wind / rh for station
        sql = (
            "SELECT MAX(CASE WHEN nat_key NOT LIKE '%|w|%' AND nat_key NOT LIKE '%|p|%' "
            "AND nat_key NOT LIKE '%|h|%' AND nat_key NOT LIKE '%|d|%' THEN value END) AS t_c, "
            "MAX(CASE WHEN nat_key LIKE '%|w|%' THEN value END) AS wind_mps, "
            "MAX(CASE WHEN nat_key LIKE '%|h|%' THEN value END) AS rh "
            "FROM tsx_observation WHERE stream_id='wx.noaa' "
            f"AND nat_key LIKE 'noaa|{station}|%'"
        )
        # parse one-line result
        import re
        raw = run_sql_capture(sql)
        m = re.search(r"t_c=([^,\)]+), wind_mps=([^,\)]+), rh=([^\)]+)", raw)
        if not m:
            print(raw or "no data")
            return 0
        def num(x):
            x = x.strip().strip("'")
            if x in ("NULL", "null", ""):
                return None
            try:
                return float(x)
            except ValueError:
                return None
        t, w, rh = num(m.group(1)), num(m.group(2)), num(m.group(3))
        if t is None:
            print("no temperature")
            return 0
        feels, how = feels_like(t, w, rh)
        print(f"{station}  temp={t:.1f}C  feels={feels:.1f}C  ({how})"
              f"  wind={w if w is not None else 'n/a'} m/s  rh={rh if rh is not None else 'n/a'}")
        return 0
    if cmd == "wxnow":
        import re
        raw = run_sql_capture(
            "SELECT substr(nat_key,1,9) AS station, "
            "MAX(CASE WHEN nat_key NOT LIKE '%|w|%' AND nat_key NOT LIKE '%|p|%' "
            "AND nat_key NOT LIKE '%|h|%' AND nat_key NOT LIKE '%|d|%' THEN value END) AS t_c, "
            "MAX(CASE WHEN nat_key LIKE '%|w|%' THEN value END) AS wind_mps, "
            "MAX(CASE WHEN nat_key LIKE '%|h|%' THEN value END) AS rh "
            "FROM tsx_observation WHERE stream_id='wx.noaa' "
            "GROUP BY substr(nat_key,1,9) ORDER BY station"
        )
        print(f"{'ST':6} {'T(C)':>6} {'feels':>6} {'wind':>6} {'RH':>6}  formula")
        for line in raw.splitlines():
            m = re.search(
                r"station='([^']+)', t_c=([^,]+), wind_mps=([^,]+), rh=([^\)]+)", line
            )
            if not m:
                continue
            st = m.group(1).replace("noaa|", "")
            def num(x):
                x = x.strip().strip("'")
                if x in ("NULL", "null", ""):
                    return None
                try:
                    return float(x)
                except ValueError:
                    return None
            t, w, rh = num(m.group(2)), num(m.group(3)), num(m.group(4))
            if t is None:
                continue
            feels, how = feels_like(t, w, rh)
            how = {"heat_index": "HI", "wind_chill": "WC", "ambient": "ambient"}.get(how, how)
            ws = f"{w:.1f}" if w is not None else "-"
            rs = f"{rh:.0f}" if rh is not None else "-"
            print(f"{st:6} {t:6.1f} {feels:6.1f} {ws:>6} {rs:>6}  {how}")
        return 0
    if cmd == "export":
        stream = argv[1] if len(argv) > 1 else "wx.noaa"
        path = argv[2] if len(argv) > 2 else f"{stream}.csv"
        import csv
        bin_path = CDB2 if os.path.isfile(CDB2) else "cdb2sql"
        r = subprocess.run(
            [bin_path, DB, "local",
             f"SELECT nat_key, ts_utc, value, unit FROM tsx_observation WHERE stream_id='{stream}' ORDER BY ts_utc"],
            capture_output=True, text=True,
        )
        n = 0
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["nat_key", "ts_utc", "value", "unit"])
            for line in (r.stdout or "").splitlines():
                if "nat_key=" not in line:
                    continue
                fields = {}
                for part in line.strip().strip("()").split(", "):
                    if "=" not in part:
                        continue
                    k, v = part.split("=", 1)
                    fields[k.strip()] = v.strip().strip("'")
                if "nat_key" not in fields:
                    continue
                w.writerow([
                    fields.get("nat_key", ""),
                    fields.get("ts_utc", ""),
                    fields.get("value", ""),
                    fields.get("unit", ""),
                ])
                n += 1
        print(f"EXPORT {stream} rows={n} file={path}")
        return 0
    if cmd == "near":
        import math
        if len(argv) < 3:
            print("usage: near <lat> <lon>", file=sys.stderr)
            return 2
        lat0, lon0 = float(argv[1]), float(argv[2])
        raw = run_sql_capture(
            "SELECT nat_key, value FROM tsx_observation "
            "WHERE stream_id='wx.noaa.meta' AND (nat_key LIKE '%|lat' OR nat_key LIKE '%|lon')"
        )
        coords = {}
        for line in raw.splitlines():
            if "nat_key=" not in line:
                continue
            fields = {}
            for part in line.strip().strip("()").split(", "):
                if "=" in part:
                    k, v = part.split("=", 1)
                    fields[k.strip()] = v.strip().strip("'")
            nk = fields.get("nat_key", "")
            if "|lat" in nk:
                coords.setdefault(nk.split("|")[1], {})["lat"] = float(fields.get("value") or 0)
            elif "|lon" in nk:
                coords.setdefault(nk.split("|")[1], {})["lon"] = float(fields.get("value") or 0)
        def hav(a, b, c, d):
            R = 6371.0
            p1, p2 = math.radians(a), math.radians(c)
            dp = math.radians(c - a)
            dl = math.radians(d - b)
            x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
            return 2 * R * math.asin(math.sqrt(x))
        rows = []
        for st, c in coords.items():
            if "lat" not in c or "lon" not in c:
                continue
            rows.append((hav(lat0, lon0, c["lat"], c["lon"]), st, c["lat"], c["lon"]))
        if not coords:
            print("no station coords in wx.noaa.meta", file=sys.stderr)
        rows.sort()
        print(f"{'ST':6} {'km':>8} {'lat':>8} {'lon':>8}")
        for d, st, la, lo in rows[:10]:
            print(f"{st:6} {d:8.1f} {la:8.3f} {lo:8.3f}")
        return 0
    if cmd == "compare":
        if len(argv) < 3:
            print("usage: compare ST1 ST2", file=sys.stderr)
            return 2
        st1, st2 = argv[1], argv[2]
        def latest(st):
            raw = run_sql_capture(
                "SELECT MAX(CASE WHEN nat_key NOT LIKE '%|w|%' AND nat_key NOT LIKE '%|p|%' "
                "AND nat_key NOT LIKE '%|h|%' AND nat_key NOT LIKE '%|d|%' THEN value END) AS t_c, "
                "MAX(CASE WHEN nat_key LIKE '%|w|%' THEN value END) AS wind_mps, "
                "MAX(CASE WHEN nat_key LIKE '%|h|%' THEN value END) AS rh "
                f"FROM tsx_observation WHERE stream_id='wx.noaa' AND nat_key LIKE 'noaa|{st}|%'"
            )
            import re
            m = re.search(r"t_c=([^,\)]+), wind_mps=([^,\)]+), rh=([^\)]+)", raw)
            if not m:
                return None
            def num(x):
                x = x.strip().strip("'")
                return None if x in ("NULL", "null", "") else float(x)
            return num(m.group(1)), num(m.group(2)), num(m.group(3))
        a, b = latest(st1), latest(st2)
        print(f"{'':8} {st1:>8} {st2:>8}")
        for label, idx in (("temp C", 0), ("wind m/s", 1), ("RH %", 2)):
            av = a[idx] if a else None
            bv = b[idx] if b else None
            fa = f"{av:.1f}" if av is not None else "-"
            fb = f"{bv:.1f}" if bv is not None else "-"
            print(f"{label:8} {fa:>8} {fb:>8}")
        if a:
            f, _ = feels_like(a[0], a[1], a[2])
            fa = f"{f:.1f}" if f is not None else "-"
        else:
            fa = "-"
        if b:
            f, _ = feels_like(b[0], b[1], b[2])
            fb = f"{f:.1f}" if f is not None else "-"
        else:
            fb = "-"
        print(f"{'feels':8} {fa:>8} {fb:>8}")
        return 0
    if cmd == "alerts-near":
        import math
        if len(argv) < 3:
            print("usage: alerts-near <lat> <lon> [km]", file=sys.stderr)
            return 2
        lat0, lon0 = float(argv[1]), float(argv[2])
        rad = float(argv[3]) if len(argv) > 3 else 150.0
        raw = run_sql_capture(
            "SELECT nat_key, payload_json FROM tsx_observation "
            "WHERE stream_id='wx.noaa.meta' AND nat_key LIKE '%|name'"
        )
        names = []
        for line in raw.splitlines():
            if "nat_key=" not in line:
                continue
            fields = {}
            for part in line.strip().strip("()").split(", "):
                if "=" in part:
                    k, v = part.split("=", 1)
                    fields[k.strip()] = v.strip().strip("'")
            st = fields.get("nat_key", "").split("|")[1] if "nat_key" in fields else ""
            info = fields.get("payload_json", "")
            # station name often like "New York, La Guardia..."
            city = info.split(",")[0].strip() if info else st
            if city and city not in ("", "null"):
                names.append((st, city))
        # fallback: if no names, use station ids only
        keys = [st for st, city in names if city and city not in ("null", "None")]
        print("near", lat0, lon0, "km", rad, "stations_meta", len(keys))
        # report nearby stations then matching alerts
        rawc = run_sql_capture(
            "SELECT nat_key, value FROM tsx_observation "
            "WHERE stream_id='wx.noaa.meta' AND (nat_key LIKE '%|lat' OR nat_key LIKE '%|lon')"
        )
        coords = {}
        for line in rawc.splitlines():
            if "nat_key=" not in line:
                continue
            fields = {}
            for part in line.strip().strip("()").split(", "):
                if "=" in part:
                    k, v = part.split("=", 1)
                    fields[k.strip()] = v.strip().strip("'")
            nk = fields.get("nat_key", "")
            if "|lat" in nk:
                coords.setdefault(nk.split("|")[1], {})["lat"] = float(fields.get("value") or 0)
            elif "|lon" in nk:
                coords.setdefault(nk.split("|")[1], {})["lon"] = float(fields.get("value") or 0)
        def hav(a, b, c, d):
            r = 6371.0
            p1, p2 = math.radians(a), math.radians(c)
            dp = math.radians(c - a)
            dl = math.radians(d - b)
            x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
            return 2 * r * math.asin(math.sqrt(x))
        near_st = [
            st for st, c in coords.items()
            if "lat" in c and "lon" in c and hav(lat0, lon0, c["lat"], c["lon"]) <= rad
        ]
        print("stations in radius", near_st[:12])
        rawa = run_sql_capture(
            "SELECT ts_utc, value AS sev, payload_json FROM tsx_observation "
            "WHERE stream_id='wx.noaa.alerts' ORDER BY ts_utc DESC LIMIT 200"
        )
        hit = 0
        for line in rawa.splitlines():
            if "payload_json=" not in line:
                continue
            low = line.lower()
            if any(st.lower() in low for st in near_st):
                print(line[:180])
                hit += 1
                if hit >= 15:
                    break
        print(f"alerts-near matched={hit}")
        return 0
    if cmd == "correlate":
        import math
        if len(argv) < 3:
            print("usage: correlate ST1 ST2", file=sys.stderr)
            return 2
        st1, st2 = argv[1], argv[2]
        def series(st):
            raw = run_sql_capture(
                "SELECT hour_utc, avg_c FROM v_hourly_wx WHERE station='noaa|" + st + "' "
                "AND avg_c IS NOT NULL ORDER BY hour_utc"
            )
            out = {}
            for line in raw.splitlines():
                if "hour_utc=" not in line:
                    continue
                fields = {}
                for part in line.strip().strip("()").split(", "):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        fields[k.strip()] = v.strip().strip("'")
                try:
                    out[fields["hour_utc"]] = float(fields.get("avg_c") or 0)
                except Exception:
                    pass
            return out
        a, b = series(st1), series(st2)
        keys = sorted(set(a) & set(b))
        n = len(keys)
        if n < 2:
            print(f"correlate {st1} {st2} n={n} (insufficient overlap)")
            return 0
        xs = [a[k] for k in keys]
        ys = [b[k] for k in keys]
        mx = sum(xs) / n
        my = sum(ys) / n
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        dy = math.sqrt(sum((y - my) ** 2 for y in ys))
        r = num / (dx * dy) if dx and dy else 0.0
        print(f"correlate {st1} vs {st2}  pearson_r={r:.4f}  n={n} hours")
        return 0
    if cmd == "help" or cmd == "-h" or cmd == "--help":
        print(__doc__)
        return 0
    if cmd == "export-all":
        outdir = argv[1] if len(argv) > 1 else "."
        os.makedirs(outdir, exist_ok=True)
        raw = run_sql_capture("SELECT DISTINCT stream_id FROM tsx_observation")
        streams = []
        for line in raw.splitlines():
            if "stream_id=" in line:
                streams.append(line.split("stream_id=", 1)[1].strip().strip(")'"))
        total = 0
        for st in streams:
            path = os.path.join(outdir, st + ".csv")
            rc = os.system(
                f"{sys.executable} {os.path.abspath(__file__)} export {st} {path} >/dev/null"
            )
            if rc == 0:
                total += 1
                print("wrote", path)
        print(f"EXPORT-ALL streams={total} dir={outdir}")
        return 0
    if cmd == "caps":
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return subprocess.call(["bash", os.path.join(root, "tools", "cap_check.sh")])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
