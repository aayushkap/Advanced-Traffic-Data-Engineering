from datetime import datetime, time as dt_time
import time
from airflow import DAG
from airflow.operators.python import PythonOperator
import json
import random
import logging
from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaProducer
from uuid import uuid4
import numpy as np

# Kafka and DAG configuration
KAFKA_BOOTSTRAP_SERVER = 'broker:29092'
DATA_PATH = '/opt/airflow/data'
NUM_RECORDS = 2500
STREM_SLEEP_TIME = 0.1


default_args = {
    'owner': 'AKAP',
    'start_date': datetime(2025, 1, 1),
}

try:
    with open(rf'{DATA_PATH}/road_data.json', 'r') as f:
        road_data = json.load(f)
except FileNotFoundError as e:
    print(f"Error: {e}. Ensure 'road_data.json' is in the correct location.")
    exit(1)



def get_data_instance(region: str, road: str):
    """
    Generates a single instance of fake traffic data for a particular region and road.
    """
    fake_vehicle_data = {}
    region_info = road_data.get(region)
    if not region_info:
        return fake_vehicle_data

    road_info = region_info.get(road)
    if not road_info:
        return fake_vehicle_data

    # Determine rush hour
    current_time = datetime.now().time()
    is_rush_hour = (
        dt_time(7, 0) <= current_time <= dt_time(9, 0) or
        dt_time(17, 0) <= current_time <= dt_time(19, 0)
    )

    # Randomly select direction
    direction = random.randint(0, 1) if road_info['bidirectional'] else 0

    # Determine vehicle type and lane preference
    if random.random() < 0.2:  # 20% chance for trucks
        vehicle_type = 'Truck'
        lane = random.randint(1, road_info['lanes'] // 2)
    else:
        vehicle_type = 'Car'
        lane = random.randint(1, road_info['lanes'])

    # Adjust speed limits based on vehicle type
    speed_limit = road_info['car_speed_limit'] if vehicle_type == 'Car' else road_info['truck_speed_limit']

    # Simulate realistic speed variations
    base_speed_variation = random.uniform(-15, 5)
    rush_hour_factor = -10 if is_rush_hour else random.uniform(-5, 0)
    lane_factor = (road_info['lanes'] - lane) * random.uniform(0.5, 1.0)

    vehicle_speed = max(0, round(speed_limit + base_speed_variation + rush_hour_factor + lane_factor))
    speeding = "sp" if vehicle_speed > speed_limit else ""

    fake_vehicle_data = {
        'id': str(uuid4()),
        'region': region,
        'road': road,
        'direction': direction,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'vehicle_type': vehicle_type,
        'lane': lane,
        'speeding': speeding,
        'velocity': vehicle_speed
    }

    return fake_vehicle_data


def create_kafka_topics():
    """
    Create Kafka topics dynamically for each road.
    """
    admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVER)
    topics = [
        NewTopic(name=f"{region}_{road.replace(' ', '')}", num_partitions=1, replication_factor=1)
        for region, roads in road_data.items()
        for road in roads.keys()
    ]

    try:
        admin_client.create_topics(new_topics=topics, validate_only=False)
        logging.info(f"Kafka topics created: {[topic.name for topic in topics]}")
    except Exception as e:
        logging.error(f"Failed to create Kafka topics: {e}")


def stream_to_kafka(region, road):
    topic_name = f"{region}_{road.replace(' ', '')}"
    producer = KafkaProducer(bootstrap_servers=[KAFKA_BOOTSTRAP_SERVER], max_block_ms=5000)
    logging.info(f"Started streaming to Kafka topic: {topic_name}")

    # Get road details including the capacity parameter
    road_info = road_data.get(region, {}).get(road, {})
    road_capacity = road_info.get('capacity', NUM_RECORDS)
    
    # Use the capacity parameter to vary the number of records
    num_records = np.random.poisson(lam=road_capacity)

    # Calculate the maximum capacity across all roads
    max_capacity = max(
        r.get('capacity', NUM_RECORDS)
        for region_val in road_data.values()
        for r in region_val.values()
    )
    # Normalize the current road's capacity relative to the maximum
    normalized_capacity = road_capacity / max_capacity if max_capacity else 1

    records_sent = 0
    while records_sent < num_records:
        data_instance = get_data_instance(region, road)
        if data_instance:
            # For busier roads (higher capacity), the delay is shorter.
            # Here, STREM_SLEEP_TIME is the base delay and the extra delay is scaled down
            delay = STREM_SLEEP_TIME + random.uniform(0, (1 - normalized_capacity) * 0.45)
            time.sleep(delay)
            producer.send(topic_name, json.dumps(data_instance).encode('utf-8'))
            records_sent += 1
    producer.flush()  # Ensure all records are sent
    logging.info(f"Finished streaming {num_records} records to Kafka topic: {topic_name}")


def submit_flink_job():
    """
    If the doris-flink job is not already running, submit it.
    """


# DAG definition
with DAG(
    'dynamic_kafka_streaming',
    schedule_interval="*/5 * * * *",  # Run every 5 minutes
    default_args=default_args,
    catchup=False,
    concurrency=4, # Limits to 4 concurrent tasks (streams)
    max_active_runs=1, # Ensures only one DAG run at a time
    description='Dynamically stream traffic data to Kafka topics.',
) as dag:

    create_topics_task = PythonOperator(
        task_id='create_kafka_topics',
        python_callable=create_kafka_topics
    )

    end_task = PythonOperator(
        task_id='end',
        python_callable=lambda: logging.info("All tasks completed.")
    )

    for region, roads in road_data.items():
        for road in roads.keys():
            stream_task = PythonOperator(
                task_id=f'stream_to_kafka_{region}_{road.replace(" ", "_")}',
                python_callable=stream_to_kafka,
                op_args=[region, road],
            )
            create_topics_task >> stream_task >> end_task
