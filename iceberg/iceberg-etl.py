import logging
import uuid
import pathway as pw
from kafka.admin import KafkaAdminClient
from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema, NestedField
from pyiceberg.types import StringType, IntegerType, FloatType, TimestampType
from pyiceberg.catalog.sql import SqlCatalog
from datetime import datetime
import pyarrow as pa
import json

# Kafka configuration
KAFKA_HOST = "broker:29092"
pw.set_license_key("FED53F-E360EF-5FA6EF-6E872B-9A5391-V3")

# Iceberg configuration
warehouse_path = "s3a://iceberg-data"
ICEBERG_CATALOG_NAME = "postgres_catalog"
POSTGRES_URI = "jdbc:postgresql://iceberg-postgres:5432/iceberg"
MINIO_BUCKET = "iceberg-data"
MINIO_S3_PATH = f"s3://{MINIO_BUCKET}/"
MINIO_ACCESS_KEY = "minio"
MINIO_SECRET_KEY = "minio123"
MINIO_ENDPOINT_URL = "http://iceberg-minio:9000"
PARTITION_SIZE = 200

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

schema = pa.schema(
    [
        pa.field("id", pa.string()),
        pa.field("region", pa.string()),
        pa.field("road", pa.string()),
        pa.field("direction", pa.int32()),
        pa.field("timestamp", pa.string()),
        pa.field("vehicle_type", pa.string()),
        pa.field("lane", pa.int32()),
        pa.field("speeding", pa.string()),
        pa.field("velocity", pa.float32()),
    ]
)

class InputSchema(pw.Schema):
    id: str
    region: str
    road: str
    direction: int
    timestamp: str
    vehicle_type: str
    lane: int
    speeding: str
    velocity: float

def setup_catalog():
    """
    Sets up the Iceberg catalog in Postgres if it doesn't already exist.
    """
    try:
        catalog = SqlCatalog(
            "default",
            **{
                "uri": "postgresql://iceberg:iceberg@postgres-iceberg:5432/iceberg",
                "warehouse": warehouse_path,
                "s3.endpoint": "http://iceberg-minio:9000",
                "s3.access-key-id": "minio",
                "s3.secret-access-key": "minio123",
            },
        )

        namespace = "default"
        if not catalog._namespace_exists(namespace):
            print(f"Namespace '{namespace}' does not exist, creating it...")
            catalog.create_namespace(namespace)
        print(f"Namespace '{namespace}' is ready!")

        logger.info("Iceberg catalog setup completed.")
        return catalog, namespace
    except Exception as e:
        logger.error(f"Error setting up Iceberg catalog: {e}")

def setup_iceberg_table(catalog, namespace):
    logger.info("Setting up Iceberg table...")
    table_name = f"{namespace}.traffic-data"
    return catalog.load_table(table_name)

def fetch_kafka_topics(bootstrap_servers: str) -> list:
    """
    Fetches the list of Kafka topics.
    """
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
        topics = [topic for topic in admin_client.list_topics() if not topic.startswith("_")]
        admin_client.close()
        return topics
    except Exception as e:
        logger.error(f"Error fetching Kafka topics: {e}")
        return []


def read_from_kafka_and_write_to_iceberg(bootstrap_servers, iceberg_table):
    """
    Reads data from Kafka and writes to Iceberg table.
    """
    topics = fetch_kafka_topics(bootstrap_servers)

    if not topics:
        logger.warning("No topics found on the Kafka broker.")
        return

    logger.info(f"Found topics: {topics}")

    rdkafka_settings = {
        "bootstrap.servers": KAFKA_HOST,
        "security.protocol": "plaintext",
        "group.id": "fixed-consumer-group",  # Should be fixed, so it knows where it left off across restarts
        "session.timeout.ms": "6000",
        "auto.offset.reset": "earliest", # Will pull from where it left off
    }

    rows = []
    def on_change(key: pw.Pointer, row: dict, time: int, is_addition: bool, rows: list = rows):
        rows.append(row)
        if len(rows) >= PARTITION_SIZE:
            insert_rows(iceberg_table, rows)
            rows.clear()
            rows = []

    def insert_rows(table, rows):
        logger.info(f"Inserting {len(rows)} records into Iceberg table...")
        try:
            arrow_table = pa.Table.from_pylist(rows, schema=schema)
            table.append(arrow_table)
        except Exception as e:
            logger.error(f"Error writing record to Iceberg table: {e}")

    def on_end():
        logger.info("End of stream.")

    for topic in topics:
        logger.info(f"Subscribing to topic: {topic}")

        pw_table = pw.io.kafka.read(
            topic=topic,
            rdkafka_settings=rdkafka_settings,
            format="json",
            schema=InputSchema,
            autocommit_duration_ms=1000,
        )

        pw.io.subscribe(pw_table, on_change, on_end)

    pw.run()

if __name__ == "__main__":
    catalog, namespace = setup_catalog()
    iceberg_table = setup_iceberg_table(catalog, namespace)
    read_from_kafka_and_write_to_iceberg(KAFKA_HOST, iceberg_table)
