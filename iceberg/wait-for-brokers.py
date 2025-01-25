import pathway as pw
from kafka.admin import KafkaAdminClient
from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema, NestedField
from pyiceberg.types import StringType, IntegerType, FloatType, TimestampType
from pyiceberg.expressions import literal
from datetime import datetime
import time


# Kafka configuration
KAFKA_HOST = "broker:29092"

RETRY_COUNT = 30
WAIT_SECONDS = 15

def fetch_kafka_topics(bootstrap_servers: str) -> list:
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
        topics = admin_client.list_topics()
        topics = [topic for topic in topics if not topic.startswith("_")]
        admin_client.close()
        return topics
    except Exception as e:
        print(f"Error fetching Kafka topics: {e}")
        return []

def main():
    for attempt in range(RETRY_COUNT):
        print(f"Attempt {attempt + 1} of {RETRY_COUNT}...")
        topics = fetch_kafka_topics(KAFKA_HOST)
        if topics:
            print(f"Kafka topics available: {topics}")
            return
        print(f"Kafka topics not available. Waiting {WAIT_SECONDS} seconds before retrying...")
        time.sleep(WAIT_SECONDS)

if __name__ == "__main__":
    main()
