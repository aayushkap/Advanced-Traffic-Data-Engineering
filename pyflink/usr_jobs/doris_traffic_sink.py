import json
import logging
from datetime import datetime

from kafka.admin import KafkaAdminClient
from pyflink.common import Row, Types, WatermarkStrategy
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import JdbcSink
from pyflink.datastream.connectors.jdbc import (
    JdbcConnectionOptions,
    JdbcExecutionOptions,
)
from pyflink.datastream.connectors.kafka import (
    DeliveryGuarantee,
    KafkaOffsetsInitializer,
    KafkaSource,
)

KAFKA_HOST = "broker:29092"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def fetch_kafka_topics(bootstrap_servers: str) -> list:
    """Fetches all topics from the Kafka broker."""
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
    topics = admin_client.list_topics()

    topics = [topic for topic in topics if not topic.startswith("_")]
    admin_client.close()
    return topics


def initialize_env() -> StreamExecutionEnvironment:
    """Initializes the Flink stream execution environment."""
    env = StreamExecutionEnvironment.get_execution_environment()

    # current dir
    root_dir_list = __file__.split("/")[:-1]
    root_dir = "/".join(root_dir_list)

    env.add_jars(
        f"file:///{root_dir}/lib/flink-connector-jdbc-3.1.2-1.18.jar",
        f"file:///{root_dir}/lib/postgresql-42.7.3.jar",
        f"file:///{root_dir}/lib/flink-sql-connector-kafka-3.1.0-1.18.jar",
        f"file:///{root_dir}/lib/mysql-connector-j-9.1.0.jar",
    )
    return env


def parse_data(data: str) -> Row:
    """Parse traffic data into a Row format."""
    try:
        data = json.loads(data)

        id = data["id"]
        region = data["region"]
        road = data["road"]
        direction = data["direction"]
        ts = str(datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S"))
        vehicle_type = data["vehicle_type"]
        lane = data["lane"]
        speeding = data["speeding"]
        velocity = data["velocity"]

        return Row(id, region, road, direction, ts, vehicle_type, lane, speeding, velocity)
    except Exception as e:
        logger.error(f"Failed to parse data: {data}. Error: {str(e)}")
        raise


def configure_doris_sink(sql_dml: str, type_info: Types) -> JdbcSink:
    """Configures the Doris sink using JDBC."""
    return JdbcSink.sink(
        sql_dml,
        type_info,
        JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
        .with_url("jdbc:mysql://doris:9030/app_db")
        .with_driver_name("com.mysql.cj.jdbc.Driver")
        .with_user_name("root")
        .with_password("")
        .build(),
        JdbcExecutionOptions.builder()
        .with_batch_interval_ms(200) # Max time to wait before sending a batch, even if the batch size is not reached
        .with_batch_size(1000) # Max number of records to send in a batch
        .with_max_retries(5)
        .build(),
    )


def configure_source(server: str, topics: list, earliest: bool = False) -> KafkaSource:
    """Initializes a Kafka source with a list of topics."""
    properties = {
        "bootstrap.servers": server,
        "group.id": "traffic-data-consumer",
        "fetch.max.wait.ms": "100", # Max wait time before fetching the next batch. Higher values means higher latency
        "max.partition.fetch.bytes": "1048576", # Max number of bytes to fetch from a partition in one request
        "fetch.min.bytes": "1048576", # Min number of bytes to fetch from a partition in one request. In MB, this is 1MB
    }

    offset = KafkaOffsetsInitializer.latest()
    if earliest:
        offset = KafkaOffsetsInitializer.earliest()

    kafka_source = (
        KafkaSource.builder()
        .set_topics(*topics)  # Dynamically subscribe to all topics
        .set_properties(properties)
        .set_starting_offsets(offset)
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )
    return kafka_source


def main() -> None:
    """Main flow controller."""

    logger.info("Initializing environment for Doris Sink")
    env = initialize_env()

    logger.info("Fetching all Kafka topics dynamically")
    topics = fetch_kafka_topics(KAFKA_HOST)
    logger.info(f"Fetched topics: {topics}")

    kafka_source = configure_source(KAFKA_HOST, topics)

    sql_dml = (
    "INSERT INTO traffic_data (id, region, road, direction, ts, vehicle_type, lane, speeding, velocity, insert_time) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())"
)
    TYPE_INFO = Types.ROW(
        [
            Types.STRING(),  # id
            Types.STRING(),  # region
            Types.STRING(),  # road
            Types.INT(),  # direction
            Types.STRING(),  # timestamp
            Types.STRING(),  # vehicle_type
            Types.INT(),  # lane
            Types.STRING(),  # speeding
            Types.FLOAT(),  # velocity
        ]
    )

    doris_sink = configure_doris_sink(sql_dml, TYPE_INFO)

    logger.info("Creating data stream from Kafka topics")
    data_stream = env.from_source(
        kafka_source, WatermarkStrategy.no_watermarks(), "Dynamic Kafka Topics"
    ).set_parallelism(4)

    env.set_parallelism(4)

    transformed_data = data_stream.map(parse_data, output_type=TYPE_INFO)

    logger.info("Adding sink to Doris")
    transformed_data.add_sink(doris_sink).set_parallelism(4)

    env.execute("Flink Doris Sink with Dynamic Kafka Topics")


if __name__ == "__main__":
    logger.info("Starting main")
    main()
