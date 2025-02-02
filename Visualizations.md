# Data Visualizations

## Columns in Dataset
Region, Timestamp, Road, ID, Direction, Vehicle Type, Lane, Speeding, Velocity, Insert Time

`Note`: Each query is done on a per road basis.
`Note`: We are adding a global time filter (Per Minute, Per Hour, Per Day) to all visualizations.
`Note`: We also by default group by vehicle type. This way we don't have to add a filter for vehicle type in every query. For queries without the filter, we just add the vehicle type columns, based of some common column, by which it was grouped. By default, Global Filter is per minute. So if for a query, we don't want to filter by vehicle type, we can just add the vehicle type column in the query. if filter is there, we just show that value, as it is already filtered by vehicle type.

## Visualizations
1. Total number of vehicles in this road. Optionally filter **vehicle type**.
`Note`: This field is not affected by the global filter. It is just a count of all vehicles in the road.
Query Type: vehicle_count
Location: Top Left (1/4)
Visualisation Type: Bar Chart / Text.

View:
```sql
CREATE MATERIALIZED VIEW vehicle_count AS
SELECT vehicle_type, COUNT(*) AS Total_Vehicles FROM traffic_data GROUP BY vehicle_type;
```

Query:  
```sql
SELECT vehicle_type, DATE_FORMAT(ts, '%Y-%m-%d %H:%i') AS time_per, COUNT(*) AS Total_Vehicles FROM traffic_data WHERE Road = 'King_Abdulaziz_Road' GROUP BY time_per, vehicle_type ORDER BY time_per, vehicle_type;
```

2. Volume of traffic in this road by time. Affected by Global Filter Optionally filter by **vehicle type**.
Query Type: traffic_volume
Type: Line Chart. Filters in seperate dropdowns.
Visualisation Type: Line Chart.

Location: Top Right (3/4)

View:
```sql
CREATE MATERIALIZED VIEW traffic_volume AS
SELECT DATE_FORMAT(ts, '%Y-%m-%d %H:%i') AS time_per, COUNT(*) AS Total_Vehicles
FROM traffic_data
GROUP BY time_per
ORDER BY time_per;
```

Query:
```sql
SELECT vehicle_type, DATE_FORMAT(ts, '%Y-%m-%d %H:%i') AS time_per, COUNT(*) AS Total_Vehicles
FROM traffic_data
WHERE road = 'King_Abdulaziz_Road'
GROUP BY time_per, vehicle_type
ORDER BY time_per, vehicle_type;

SELECT vehicle_type, DATE_FORMAT(ts, '%Y-%m-%d %H') AS time_per, COUNT(*) AS Total_Vehicles
FROM traffic_data
WHERE road = 'King_Abdulaziz_Road'
GROUP BY time_per, vehicle_type
ORDER BY time_per, vehicle_type;

SELECT vehicle_type, DATE_FORMAT(ts, '%Y-%m-%d') AS time_per, COUNT(*) AS Total_Vehicles
FROM traffic_data
WHERE road = 'King_Abdulaziz_Road'
GROUP BY time_per, vehicle_type
ORDER BY time_per, vehicle_type;
```

3. Average speed of vehicles. Affected by Global Filter and **vehicle_type**.
Query Type: average_speed
Type: Text. Filters in seperate dropdowns. Show speed limit, number of speeding vehicles.
Visualisation Type: Text / Line Chart.

Query:
```sql
SELECT vehicle_type, DATE_FORMAT(ts, '%Y-%m-%d %H:%i') AS time_per, AVG(velocity) AS Average_Speed
FROM traffic_data
WHERE road = 'King_Abdulaziz_Road'
GROUP BY time_per, vehicle_type
ORDER BY time_per, vehicle_type;
```

4.  Lane utilization for a road. Affected by Global Filter.
Query Type: lane_utilization
Type: Pie Chart.
Visualisation Type: Pie Chart.

Query:
```sql
SELECT vehicle_type, DATE_FORMAT(ts, '%Y-%m-%d %H:%i') AS time_per, lane, COUNT(*) AS vehicle_count
FROM traffic_data
WHERE road = 'King_Abdulaziz_Road'
GROUP BY time_per, lane, vehicle_type 
ORDER BY time_per, lane, vehicle_type;
```

