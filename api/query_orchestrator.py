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

        self.base_queries = {
            "traffic_volume": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, COUNT(*) AS traffic_volume FROM traffic_data WHERE road = %s",
            "average_speed": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, AVG(velocity) AS average_speed FROM traffic_data WHERE road = %s",
            "speeding_vehicles": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, COUNT(*) AS speeding_vehicles FROM traffic_data WHERE road = %s AND speeding <> ''",
            "lane_utilization": "SELECT vehicle_type, DATE_FORMAT(ts, %s) AS time_per, lane, COUNT(*) AS vehicle_count FROM traffic_data WHERE road = %s"
        }
