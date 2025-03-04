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

def get_data_instance(region: str, road: str, max_capacity: int, is_raining: bool):
    """
    Generates a single instance of fake traffic data with enhanced variability.
    """
    fake_vehicle_data = {}
    region_info = road_data.get(region)
    if not region_info:
        return fake_vehicle_data

    road_info = region_info.get(road)
    if not road_info:
        return fake_vehicle_data

    current_datetime = datetime.now()
    current_time = current_datetime.time()
    is_weekend = current_datetime.weekday() >= 5  # Saturday or Sunday

    # Determine time period
    if dt_time(22, 0) <= current_time or current_time <= dt_time(6, 0):
        period = 'night'
    elif dt_time(7, 0) <= current_time <= dt_time(9, 0):
        period = 'morning_rush'
    elif dt_time(17, 0) <= current_time <= dt_time(19, 0):
        period = 'evening_rush'
    elif dt_time(9, 0) < current_time < dt_time(17, 0):
        period = 'midday'
    else:
        period = 'evening'

    # Congestion factor based on road capacity
    congestion_factor = max_capacity / road_info['capacity']

    # Adjust rush hour factor based on period and weekend
    if period in ['morning_rush', 'evening_rush']:
        rush_hour_factor = np.random.normal(-10 * congestion_factor, 5) if not is_weekend else np.random.normal(-5 * congestion_factor, 5)
    elif period == 'night':
        rush_hour_factor = np.random.normal(5, 5)  # Higher speeds at night
    else:
        rush_hour_factor = np.random.normal(0, 5)

    # Weather factor (10% chance of rain per batch)
    weather_factor = -10 if is_raining else 0

    # Direction for bidirectional roads
    direction = random.randint(0, 1) if road_info['bidirectional'] else 0

    # Vehicle type and lane preference
    if random.random() < 0.2:  # 20% chance for trucks
        vehicle_type = 'Truck'
        lane = random.randint(1, max(1, road_info['lanes'] // 2))  # Ensure at least lane 1
    else:
        vehicle_type = 'Car'
        lane = random.randint(1, road_info['lanes'])

    # Speed limit based on vehicle type
    speed_limit = road_info['car_speed_limit'] if vehicle_type == 'Car' else road_info['truck_speed_limit']

    # Base speed variation using normal distribution
    base_speed_variation = np.random.normal(0, 5)

    # Lane factor: inner lanes (lower numbers) are faster
    lane_factor = (road_info['lanes'] - lane) * np.random.normal(0.5, 0.1)

    # Calculate vehicle speed
    vehicle_speed = speed_limit + base_speed_variation + rush_hour_factor + lane_factor + weather_factor
    vehicle_speed = max(0, round(vehicle_speed))

    # Determine if speeding
    speeding = "sp" if vehicle_speed > speed_limit else ""

    fake_vehicle_data = {
        'id': str(uuid4()),
        'region': region,
        'road': road,
        'direction': direction,
        'timestamp': current_datetime.strftime('%Y-%m-%d %H:%M:%S'),
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
    """
    Stream traffic data to Kafka with increased variation in volume and timing.
    """
    topic_name = f"{region}_{road.replace(' ', '')}"
    producer = KafkaProducer(bootstrap_servers=['broker:29092'], max_block_ms=5000)
    logging.info(f"Started streaming to Kafka topic: {topic_name}")

    # Get road-specific data
    road_info = road_data.get(region, {}).get(road, {})
    road_capacity = road_info.get('capacity', 2500)

    max_capacity = max(
        r.get('capacity', 2500)
        for region_val in road_data.values()
        for r in region_val.values()
    )

    # Determine time period and base lambda
    current_time = datetime.now().time()
    if dt_time(7, 0) <= current_time <= dt_time(9, 0) or dt_time(17, 0) <= current_time <= dt_time(19, 0):
        period = 'rush_hour'
        lambda_base = road_capacity * 1.2
    elif dt_time(22, 0) <= current_time or current_time <= dt_time(6, 0):
        period = 'night'
        lambda_base = road_capacity * 0.5
    else:
        period = 'normal'
        lambda_base = road_capacity

    # Add random variation to lambda (between 80% and 120% of base)
    lambda_adjusted = lambda_base * np.random.uniform(0.8, 1.2)
    num_records = np.random.poisson(lam=lambda_adjusted)

    is_raining = random.random() < 0.1

    # Calculate mean inter-arrival time for the 5-minute window
    if num_records > 0:
        mean_inter_arrival = 300 / num_records  # in seconds
    else:
        mean_inter_arrival = 0

    # Stream records with variable delays
    records_sent = 0
    while records_sent < num_records:
        data_instance = get_data_instance(region, road, max_capacity, is_raining)
        if data_instance:
            if records_sent > 0:
                # Use lognormal distribution for delay, capped at 10 seconds
                delay = np.random.lognormal(mean=np.log(mean_inter_arrival), sigma=0.5)
                delay = min(delay, 10)
                time.sleep(delay)
            producer.send(topic_name, json.dumps(data_instance).encode('utf-8'))
            records_sent += 1
    producer.flush()
    logging.info(f"Finished streaming {num_records} records to Kafka topic: {topic_name}")

def submit_flink_job():
    """
    Placeholder for Flink job submission logic.
    """
    pass

# DAG definition
with DAG(
    'dynamic_kafka_streaming',
    schedule_interval="*/5 * * * *",  # Run every 5 minutes
    default_args=default_args,
    catchup=False,
    concurrency=4,  # Adjust if more roads are added
    max_active_runs=1,
    description='Dynamically stream traffic data to Kafka topics with enhanced variability.',
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