import pymysql

class TrafficDataQueryBuilder:
    def __init__(self, host='localhost', port=9030, user='root', password='', database='app_db'):
        self.connection_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'cursorclass': pymysql.cursors.DictCursor
        }

        self.base_queries = {
            "total_vehicle_count": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, COUNT(*) AS total_vehicle_count FROM traffic_data WHERE road = %s",
            "traffic_volume": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, COUNT(*) AS traffic_volume FROM traffic_data WHERE road = %s",
            "average_speed": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, AVG(velocity) AS average_speed FROM traffic_data WHERE road = %s",
            "speeding_vehicles": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, COUNT(*) AS speeding_vehicles FROM traffic_data WHERE road = %s AND speeding <> ''",
            "lane_utilization": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, lane, COUNT(*) AS vehicle_count FROM traffic_data WHERE road = %s"
        }


    def build_sql_query(self, query_type, road, time_granularity="Per Minute", history=10, filters=None):
        """
        Build SQL query based on query type, road, and optional filters.
        This version appends a condition that limits results to the most recent
        time buckets. It uses the DATE_FORMAT(ts, ...) expression (instead of the alias)
        in the WHERE clause so that the SQL is valid.
        """
        # Mapping for time formats
        time_format_mapping = {
            "Per Minute": "%Y-%m-%d %H:%i",
            "Per Hour": "%Y-%m-%d %H",
            "Per Day": "%Y-%m-%d"
        }
        
        # Validate query type
        if query_type not in self.base_queries:
            raise ValueError(f"Invalid query type: {query_type}")
        
        # Get the base query and time format
        sql = self.base_queries[query_type]
        time_format = time_format_mapping.get(time_granularity, "%Y-%m-%d %H:%i")
        
        # Base parameters: the base query is assumed to have DATE_FORMAT(ts, %s) and road = %s
        params = [time_format, road]
        
        # Apply additional filters (if any)
        conditions = []
        if filters:
            for key, value in filters.items():
                conditions.append(f"{key} = %s")
                params.append(value)
        
        # Build additional conditions from filters (if any)
        where_clause = " AND ".join(conditions)
        
        # Add the history condition if requested.
        # We use DATE_FORMAT(ts, %s) in the outer condition so that we compare against the
        # same formatted value produced in the SELECT.
        if history:
            history_subquery = (
                "DATE_FORMAT(ts, %s) IN ("
                "SELECT DISTINCT time_per FROM ("
                "    SELECT DATE_FORMAT(ts, %s) AS time_per "
                "    FROM traffic_data "
                "    WHERE road = %s "
                "    GROUP BY time_per "
                "    ORDER BY time_per DESC "
                f"    LIMIT {history} "
                ") subquery)"
            )
            # Append the history condition with an AND if any other conditions exist
            if where_clause:
                where_clause = f"{where_clause} AND {history_subquery}"
            else:
                where_clause = history_subquery
            
            # Extend parameters:
            # • For the outer DATE_FORMAT(ts, %s) we need one time_format
            # • For the inner SELECT's DATE_FORMAT(ts, %s) we need a second time_format
            # • For the inner WHERE road = %s we need road
            params.extend([time_format, time_format, road])
        
        # Append the additional conditions to the base query.
        # (Assumes that self.base_queries already contain a WHERE clause.)
        final_query = f"{sql} {'AND' if where_clause else ''} {where_clause}"
        
        # Append the GROUP BY / ORDER BY clause.
        if query_type == "lane_utilization":
            final_query = f"{final_query} GROUP BY vehicle_type, time_per, lane ORDER BY vehicle_type, time_per, lane"
        else:
            final_query = f"{final_query} GROUP BY vehicle_type, time_per ORDER BY vehicle_type, time_per"
        
        return final_query.strip(), params


    def execute_query(self, sql_query, params):
        """
        Execute the SQL query and return results.
        """
        print(f"Executing query: {sql_query} with params: {params}")
        try:
            with pymysql.connect(**self.connection_params) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql_query, params)
                    results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Database query failed: {e}")
            return []

    def query_orchestrator(self, query_key):
        """
        Main handler for parsing query keys, building SQL queries, and processing results.
        """

        results = {}

        # Example key format: King_Abdulaziz_Road;Per Minute;vehicle_type=Car
        parts = query_key.split(";")
        road = parts[0].split(":")
        time_granularity = parts[1].split("=")[-1]
        history = parts[2].split("=")[-1]

        print(f"Processing query key: {query_key}")
        print(f"Road: {road}, Time Granularity: {time_granularity}, History: {history}")

        for query_type in self.base_queries.keys():
            try:
                # Extract optional filters
                filters = {}
                for part in parts[3:]:
                    key, value = part.split("=")
                    filters[key] = value

                # Build SQL query
                sql_query, params = self.build_sql_query(query_type, road, time_granularity, history, filters)
                
                # Fetch results
                result = self.execute_query(sql_query, params)
                results[query_type] = result
            except (ValueError, IndexError) as e:
                print(f"Error processing query key: {e}")
                results[query_type] = []
        return results
            
if __name__ == "__main__":
    query_builder = TrafficDataQueryBuilder()
    results = query_builder.query_orchestrator("King_Abdulaziz_Road;Per Minute;")
    print(results)
            
            