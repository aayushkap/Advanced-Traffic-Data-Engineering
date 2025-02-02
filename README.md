
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
    insert_time IS NOT NULL ;

SELECT COUNT(*) AS record_count
FROM traffic_data
WHERE insert_time >= (
        SELECT MIN(insert_time) 
        FROM traffic_data
    )
  AND insert_time < (
        SELECT DATE_ADD(MIN(insert_time), INTERVAL 1 HOUR) 
        FROM traffic_data
    );

SELECT insert_time, COUNT(*) AS total_vehicles
FROM traffic_data
GROUP BY insert_time
ORDER BY insert_time desc;
"

> In Doris, when you create a materialized view (MV), you query the base table, and the Doris query optimizer automatically decides whether to use the materialized view to answer your query. The materialized view itself is not directly queried by name, as Doris abstracts its usage.

3. Submit Doris job: docker compose exec flink-jobmanager flink run -p 4 -py /opt/flink/usr_jobs/doris_traffic_sink.py






I am trying to create an admin dashboad, with a table that has the schema:

Field	Type	Null	Extra	Default	Key	
region	varchar(50)	Yes			true
ts	varchar(50)	Yes			true
road	varchar(50)	Yes			true
id	varchar(50)	Yes	NONE		false
direction	int	Yes	NONE		false
vehicle_type	varchar(50)	Yes	NONE		false
lane	int	Yes	NONE		false

I want to display all sorts of information using the above schema, using all sorts of creative visualizations. There can also be filters on the visualizations. Eg: filter vehicle type by all, cars,trucks etc. There are multiple regions and those regions have multiple roads in them.

Sample Data:

egion	ts	road	id	direction	vehicle_type	lane	speeding	velocity	insert_time
Mecca	2025-01-26 09:25:17	Al_Haram_Road	4dda6812-17ad-4b13-92b8-ef1ad16f9c40	1	Car	1	sp	63	2025-01-26 09:25:19
Mecca	2025-01-26 09:25:17	Al_Haram_Road	a947dda2-141e-4a38-a721-8dd698c2bf29	0	Truck	1		39	2025-01-26 09:25:18
Mecca	2025-01-26 09:25:17	Umm_Al_Qura_Road	12796933-d47d-4f0a-a345-d7a9e3097268	0	Car	2		94	2025-01-26 09:25:19
Mecca	2025-01-26 09:25:17	Umm_Al_Qura_Road	8bfc8e22-23e0-4734-82af-f5c927427c8f	0	Car	4	sp	103	2025-01-26 09:25:18
Mecca	2025-01-26 09:25:18	Al_Haram_Road	c4d85a41-fbe2-4043-b681-d190196b1601	1	Car	2		39	2025-01-26 09:25:20
Mecca	2025-01-26 09:25:18	Al_Haram_Road	e41bfc9a-1d8f-48bd-b4ef-72e93450d12b	0	Truck	1		35	2025-01-26 09:25:20
Mecca	2025-01-26 09:25:18	Umm_Al_Qura_Road	69fded16-14f7-49fc-88fb-2958d3be95b6	0	Car	2	sp	103	2025-01-26 09:25:20


Use the given information to design creative and important visualizations and provide sql queries for them. the table is traffic_data. Where relevant , create filters and give the sql for the filters applied as well. 
