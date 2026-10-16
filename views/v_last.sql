-- Apply with tools/apply_views.sh (one CREATE VIEW per cdb2sql call)
-- v_last / v_stats terminal views (tsx#3)
-- Table names match sql/schema.sql (tsx_*).
CREATE VIEW v_last AS
SELECT stream_id, nat_key, ts_utc, value, unit
FROM tsx_observation
ORDER BY ts_utc DESC
LIMIT 50;

CREATE VIEW v_last_eq AS
SELECT nat_key, ts_utc, value, unit
FROM tsx_observation
WHERE stream_id = 'eq.usgs'
ORDER BY ts_utc DESC
LIMIT 50;

CREATE VIEW v_last_wx AS
SELECT nat_key, ts_utc, value, unit
FROM tsx_observation
WHERE stream_id = 'wx.noaa'
ORDER BY ts_utc DESC
LIMIT 50;

CREATE VIEW v_stats AS
SELECT stream_id,
       COUNT(*) AS n,
       MIN(ts_utc) AS first_ts,
       MAX(ts_utc) AS last_ts,
       AVG(value) AS avg_val,
       MAX(value) AS max_val
FROM tsx_observation
GROUP BY stream_id;

CREATE VIEW v_stats_hourly AS
SELECT stream_id,
       substr(ts_utc, 1, 13) AS hour_utc,
       COUNT(*) AS n,
       AVG(value) AS avg_val
FROM tsx_observation
GROUP BY stream_id, substr(ts_utc, 1, 13);

CREATE VIEW v_series AS
SELECT stream_id, code, title FROM tsx_series;

CREATE VIEW v_stream AS
SELECT stream_id, title, grain FROM tsx_stream;

CREATE VIEW v_stats_wx AS
SELECT substr(nat_key, 1, 12) AS station,
       COUNT(*) AS n,
       MAX(ts_utc) AS last_ts,
       AVG(value) AS avg_c,
       MIN(value) AS min_c,
       MAX(value) AS max_c
FROM tsx_observation
WHERE stream_id = 'wx.noaa'
GROUP BY substr(nat_key, 1, 12);

CREATE VIEW v_hourly_wx AS
SELECT substr(nat_key, 1, 9) AS station,
       substr(ts_utc, 1, 13) AS hour_utc,
       AVG(CASE WHEN nat_key NOT LIKE '%|w|%' AND nat_key NOT LIKE '%|p|%' THEN value END) AS avg_c,
       AVG(CASE WHEN nat_key LIKE '%|w|%' THEN value END) AS avg_wind_mps,
       AVG(CASE WHEN nat_key LIKE '%|p|%' THEN value END) AS avg_hpa,
       COUNT(*) AS n
FROM tsx_observation
WHERE stream_id = 'wx.noaa'
GROUP BY substr(nat_key, 1, 9), substr(ts_utc, 1, 13);
