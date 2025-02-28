"""
Queries:

1. Total Number Of Vehicles (Date) (Vehicle Type)
2. Total Number Of (Date) (Vehicle Type)
"""

import pymysql

class TrafficDataQueryBuilder:
    def __init__(self, host='doris', port=9030, user='root', password='', database='app_db'):
        self.connection_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'cursorclass': pymysql.cursors.DictCursor
        }

        try:
            self.connection = pymysql.connect(**self.connection_params)
        except Exception as e:
            print(f"Database connection failed: {e}")
            exit(1)

        self.base_queries = {
            "traffic_volume": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, COUNT(*) AS traffic_volume FROM traffic_data WHERE road = %s",
            "average_speed": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, AVG(velocity) AS average_speed FROM traffic_data WHERE road = %s",
            "speeding_vehicles": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, COUNT(*) AS speeding_vehicles FROM traffic_data WHERE road = %s AND speeding <> ''",
            "total_speeding_vehicles": "SELECT DATE_FORMAT(ts, %s) AS time_per, COUNT(*) AS total_speeding_vehicles FROM traffic_data WHERE road = %s AND speeding <> ''",
            "lane_utilization": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, lane, COUNT(*) AS vehicle_count FROM traffic_data WHERE road = %s"
        }

    def get_metadata(self):
        """
        Get metadata for the traffic data.
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * from road_metadata ORDER BY region, road ASC")
                data = cursor.fetchall()
                return data
        except Exception as e:
            print(f"Database (Metadata) query failed: {e}")
            return []

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
        if query_type not in ["lane_utilization", "traffic_volume", "speeding_vehicles", "average_speed", "total_speeding_vehicles"] and filters:
            for key, value in filters.items():
                conditions.append(f"{key} = %s")
                params.append(value)
        
        # Build additional conditions from filters (if any)
        where_clause = " AND ".join(conditions)
        
        # These queries only require the latest data, so we limit the results to the most recent time buckets.
        if query_type in ["total_vehicle_count", "speeding_vehicles", "lane_utilization", "average_speed"]:
            history = 1
        
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
            # For the outer DATE_FORMAT(ts, %s) we need one time_format
            # For the inner SELECT's DATE_FORMAT(ts, %s) we need a second time_format
            # For the inner WHERE road = %s we need road
            params.extend([time_format, time_format, road])
        
        # Append the additional conditions to the base query.
        # (Assumes that self.base_queries already contain a WHERE clause.)
        final_query = f"{sql} {'AND' if where_clause else ''} {where_clause}"
        
        # Append the GROUP BY / ORDER BY clause.
        if query_type == "lane_utilization":
            final_query = f"{final_query} GROUP BY vehicle_type, time_per, lane ORDER BY vehicle_type, time_per, lane"
        elif query_type in ["total_speeding_vehicles"]:
            final_query = f"{final_query} GROUP BY time_per ORDER BY time_per"
        else:
            final_query = f"{final_query} GROUP BY vehicle_type, time_per ORDER BY vehicle_type, time_per"
        
        return final_query.strip(), params


    def execute_query(self, sql_query, params):
        """
        Execute the SQL query and return results.
        """
        try:
            # Format query with parameters for debugging
            formatted_query = sql_query
            for param in params:
                formatted_query = formatted_query.replace('%s', f"'{param}'", 1)
            
            with self.connection.cursor() as cursor:
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

        # Example key format: King_Abdulaziz_Road;Per Minute;history=10;vehicle_type=Car
        parts = query_key.split(";")
        road = parts[0].split(":")[0]
        time_granularity = parts[1].split("=")[-1]
        history = parts[2].split("=")[-1]

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
    results = query_builder.query_orchestrator("Umm_Al_Qura_Road;Per Minute;history=5;vehicle_type=Car")
            