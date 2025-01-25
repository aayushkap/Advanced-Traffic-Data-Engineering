
Commands:

1.  docker-compose up -d --build

2. In Doris: http://localhost:8030/

"
CREATE DATABASE app_db;

USE app_db;

CREATE TABLE traffic_data (
    region VARCHAR(50), -- Specify the maximum length
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


CREATE MATERIALIZED VIEW max_test AS
SELECT 
    region,
    road,
    COUNT(*) AS total_vehicles, 
FROM traffic_data
GROUP BY region, road;

SELECT region, road, COUNT(*) AS total_vehicles
FROM traffic_data
GROUP BY region, road;

SELECT 
    AVG(TIMESTAMPDIFF(SECOND, ts, insert_time)) AS avg_time_difference
FROM 
    traffic_data
WHERE 
    insert_time IS NOT NULL 
    AND insert_time >= '2025-01-02 08:40:00';

SELECT insert_time, COUNT(*) AS total_vehicles
FROM traffic_data
GROUP BY insert_time
ORDER BY insert_time desc;
"

> In Doris, when you create a materialized view (MV), you query the base table, and the Doris query optimizer automatically decides whether to use the materialized view to answer your query. The materialized view itself is not directly queried by name, as Doris abstracts its usage.

3. Submit Doris job: docker compose exec flink-jobmanager flink run -py /opt/flink/usr_jobs/doris_traffic_sink.py
