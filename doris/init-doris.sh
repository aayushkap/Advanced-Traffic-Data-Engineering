#!/bin/bash

echo "Waiting for Doris to be ready..."
while ! nc -z localhost 9030; do
    sleep 2
done

echo "Doris is up. Running initialization commands..."
mysql -h 127.0.0.1 -P 9030 -uroot <<EOF
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
EOF
echo "Initialization complete."
