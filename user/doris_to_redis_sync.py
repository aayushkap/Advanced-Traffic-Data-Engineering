import pymysql

connection = pymysql.connect(
    host='localhost', 
    port=9030,          
    user='root',       
    password='',        
    database='app_db',  
    cursorclass=pymysql.cursors.DictCursor  # to dict
)

def build_sql_query(query_type, road, time_granularity="Per Minute", filters=None):
    """
    Build SQL query based on query type, road, and optional filters.
    """
    print("\n Building SQL Query")
    time_format_mapping = {
        "Per Minute": "%Y-%m-%d %H:%i",
        "Per Hour": "%Y-%m-%d %H",
        "Per Day": "%Y-%m-%d"
    }
    
    base_queries = {
        "vehicle_count": "SELECT vehicle_type, COUNT(*) AS Total_Vehicles FROM traffic_data WHERE road = '{road}'",
        "traffic_volume": "SELECT vehicle_type, DATE_FORMAT(ts, '{time_format}') AS time_per, COUNT(*) AS Total_Vehicles FROM traffic_data WHERE road = '{road}'",
        "average_speed": "SELECT vehicle_type, DATE_FORMAT(ts, '{time_format}') AS time_per, AVG(velocity) AS Average_Speed FROM traffic_data WHERE road = '{road}'",
        "lane_utilization": "SELECT vehicle_type, DATE_FORMAT(ts, '{time_format}') AS time_per, lane, COUNT(*) AS vehicle_count FROM traffic_data WHERE road = '{road}'"
    }

    # Special case for vehicle count query
    if query_type == "vehicle_count":
        
        # Check if vehicle type filter is present
        if "vehicle_type" in filters:
            vehicle_type = filters["vehicle_type"]
            return f"{base_queries[query_type].format(road=road)} AND vehicle_type = '{vehicle_type}' GROUP BY vehicle_type"
        return f"{base_queries[query_type].format(road=road)} GROUP BY vehicle_type"

    # Get base SQL query
    sql = base_queries[query_type].format(road=road, time_format=time_format_mapping.get(time_granularity, "%Y-%m-%d %H:%i"))
    print("\n\t", sql)

    # Apply additional filters
    conditions = []
    if filters:
        for key, value in filters.items():
            conditions.append(f"{key} = '{value}'")

    where_clause = " AND ".join(conditions) if conditions else ""
    
    # Group and order clauses
    group_order_clause = "GROUP BY time_per, vehicle_type ORDER BY time_per, vehicle_type"
    if query_type == "lane_utilization":
        group_order_clause = "GROUP BY time_per, vehicle_type, lane ORDER BY time_per, vehicle_type, lane"
    final_query = f"{sql} {'AND' if where_clause else ''} {where_clause} {group_order_clause}"
    print("\n\t", final_query)
    return final_query.strip()

def process_results(results, sum_vehicle_types=False):
    """
    Process query results, optionally summing across vehicle types.
    """
    if not results:
        return []

    # Sum across vehicle types if required
    processed_data = {}
    for row in results:
        vehicle_type, time_per, count_or_speed = row

        if sum_vehicle_types:
            if time_per not in processed_data:
                processed_data[time_per] = 0
            processed_data[time_per] += count_or_speed
        else:
            if time_per not in processed_data:
                processed_data[time_per] = {}
            processed_data[time_per][vehicle_type] = count_or_speed

    return processed_data

def execute_query(sql_query):
    results = None
    try:
        with connection.cursor() as cursor:
            query = sql_query
            cursor.execute(query)
            results = cursor.fetchall()
    finally:
        connection.close()
    return results

def query_orchestrator(query_key):
    """
    Main handler for parsing query keys, building SQL queries, and processing results.
    """
    # Example key format: vehicle_count:King_Abdulaziz_Road;Per Minute;vehicle_type=Car
    parts = query_key.split(";")

    print("\t", parts)
    
    # Extract query type and road
    query_type, road = parts[0].split(":")
    time_granularity = parts[1].split("=")[-1]

    print("\n\t", query_type, road, time_granularity)
    
    # Extract optional filters
    filters = {}
    for part in parts[2:]:
        key, value = part.split("=")
        filters[key] = value

    print("\n\t", filters)

    # Build SQL query
    sql_query = build_sql_query(query_type, road, time_granularity, filters)
    
    # Fetch and process results
    results = execute_query(sql_query)

    print("\n\t", results)

    # Determine if vehicle types should be summed based on the presence of a filter
    sum_vehicle_types = "vehicle_type" not in filters
    # processed_data = process_results(results, sum_vehicle_types)
    return results

# Example Usage
query_key = "vehicle_count:King_Abdulaziz_Road;Per Minute;vehicle_type=Car"
result = query_orchestrator(query_key)
print("Processed Query Result:", result)
