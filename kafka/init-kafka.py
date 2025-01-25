import logging
import json
from kafka.admin import KafkaAdminClient, NewTopic

KAFKA_BOOTSTRAP_SERVER = 'broker:29092'

# In the container, the road data is stored in the data sub-directory.
try:
    with open(r'/init-kafka/data/road_data.json', 'r') as f:
        road_data = json.load(f)
except FileNotFoundError as e:
    print(f"Error: {e}. Ensure 'road_data.json' is in the correct location.")
    exit(1)

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
        print(f"Kafka topics created: {[topic.name for topic in topics]}")
    except Exception as e:
        print(f"Failed to create Kafka topics: {e}")

if __name__ == '__main__':
    create_kafka_topics()
    print("Kafka topics created successfully.")