CREATE DATABASE app_db;

USE app_db;

CREATE TABLE traffic_data (
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
