CREATE DATABASE IF NOT EXISTS app_db;

USE app_db;

CREATE TABLE IF NOT EXISTS traffic_data (
    region VARCHAR(50),
    ts VARCHAR(50),
    road VARCHAR(50),
    id VARCHAR(50),
    direction INT,
    vehicle_type VARCHAR(50),
    lane INT,
    speeding VARCHAR(50),
    velocity FLOAT,
    insert_time DATETIME
)
DUPLICATE KEY(region, ts, road)
DISTRIBUTED BY HASH(region) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);

CREATE MATERIALIZED VIEW vehicle_count AS
SELECT Vehicle_Type, COUNT(*) AS Total_Vehicles FROM traffic_data GROUP BY Vehicle_Type;

CREATE MATERIALIZED VIEW traffic_volume AS
SELECT DATE_FORMAT(ts, '%Y-%m-%d %H:%i') AS Time_Per_Minute, COUNT(*) AS Total_Vehicles
FROM traffic_data
GROUP BY Time_Per_Minute
ORDER BY Time_Per_Minute;
