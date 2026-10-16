-- P0 demo: hourly count + avg magnitude (tsx#1)
-- Run: python3 query/tsx_cli.py hourly eq.usgs
SELECT * FROM v_stats_hourly WHERE stream_id = 'eq.usgs'
ORDER BY hour_utc DESC LIMIT 24;
