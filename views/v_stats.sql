-- hourly aggregates (demo)
CREATE VIEW v_eq_hourly AS
SELECT
  CAST(strftime('%Y-%m-%dT%H:00:00Z', ts_utc) AS VARCHAR(20)) AS hour_utc,
  COUNT(*) AS n,
  AVG(value) AS avg_mag,
  MAX(value) AS max_mag
FROM observation
WHERE stream_id = 'eq.usgs'
GROUP BY 1;

CREATE VIEW v_eq_last AS
SELECT nat_key, ts_utc, value, unit, payload_json
FROM observation
WHERE stream_id = 'eq.usgs'
ORDER BY ts_utc DESC
LIMIT 100;
