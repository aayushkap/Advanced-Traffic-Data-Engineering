CREATE TABLE traffic_data (
    region VARCHAR(255),
    road VARCHAR(255),
    direction INT,
    ts VARCHAR(50),
    vehicle_type VARCHAR(50),
    lane INT,
    speeding VARCHAR(10),
    velocity FLOAT
);

\d traffic_data
