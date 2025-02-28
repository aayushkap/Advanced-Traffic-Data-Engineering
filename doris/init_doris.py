import pymysql
import time
import json

def wait_for_backends(conn):
    """Wait until at least one Doris backend is active."""
    print("Waiting for Doris BE to come online...")
    while True:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW BACKENDS;")
                results = cursor.fetchall()
                # Check if any cell in the result contains the text "true"
                if any("true" in str(col).lower() for row in results for col in row):
                    print("Doris BE is online.")
                    break
        except Exception as e:
            print("Error checking backends:", e)
        time.sleep(5)

def wait_for_doris_ready(conn):
    """Wait until Doris is fully ready by executing a simple query."""
    print("Waiting for Doris to be ready...")
    while True:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                if cursor.fetchone() is not None:
                    print("Doris is ready.")
                    break
        except Exception as e:
            print("Error checking Doris readiness:", e)
        time.sleep(5)

def run_initialization(conn, sql_commands):
    """Execute the provided SQL commands one-by-one."""
    with conn.cursor() as cursor:
        for statement in sql_commands.split(';'):
            stmt = statement.strip()
            if stmt:
                print("Executing:", stmt)
                cursor.execute(stmt)
        conn.commit()
    print("Initialization complete.")

def load_road_metadata(conn, json_file='road_data.json'):
    # Create the metadata table if it doesn't exist.
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS road_metadata (
        region VARCHAR(50),
        road VARCHAR(50),
        car_speed_limit INT,
        truck_speed_limit INT,
        lanes INT
    )
    UNIQUE KEY(region, road)
    DISTRIBUTED BY HASH(region) BUCKETS 3
    PROPERTIES (
        "replication_allocation" = "tag.location.default: 1"
    );
    """
    with conn.cursor() as cursor:
        cursor.execute(create_table_sql)
    conn.commit()
    
    # Read and parse the JSON file.
    with open(json_file, 'r') as f:
        road_data = json.load(f)
    
    # Prepare the INSERT SQL statement.
    insert_sql = """
    INSERT INTO road_metadata (region, road, car_speed_limit, truck_speed_limit, lanes)
    VALUES (%s, %s, %s, %s, %s);
    """
    
    # Insert each road's metadata into the table.
    with conn.cursor() as cursor:
        for region, roads in road_data.items():
            for road, details in roads.items():
                car_speed_limit = details.get('car_speed_limit')
                truck_speed_limit = details.get('truck_speed_limit')
                lanes = details.get('lanes')
                cursor.execute(insert_sql, (region, road, car_speed_limit, truck_speed_limit, lanes))
    conn.commit()

if __name__ == "__main__":
    # Attempt to connect until the Doris service is available.
    print("Connecting to Doris at host 'doris', port 9030...")
    while True:
        try:
            conn = pymysql.connect(
                host='doris',
                port=9030,
                user='root',
                password='',
                autocommit=True
            )
            print("Connected to Doris.")
            break
        except Exception as e:
            print("Could not connect to Doris, retrying...", e)
            time.sleep(5)
    
    # Wait for active backends and for Doris readiness.
    wait_for_backends(conn)
    wait_for_doris_ready(conn)
    
    # Define your initialization SQL commands.
    sql_commands = """
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
    """
    
    # Run the initialization SQL.
    run_initialization(conn, sql_commands)
    load_road_metadata(conn)
    conn.close()
