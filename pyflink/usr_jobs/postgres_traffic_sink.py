import json
import logging
from datetime import datetime

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
    KafkaRecordSerializationSchema,
    KafkaSink,
    KafkaSource,
)

KAFKA_HOST = "broker:29092"
POSTGRES_HOST = "postgres2:5432"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def parse_data(data: str) -> Row:
    """Parse traffic data into a Row format."""
    logger.info("In parse_data")
    logger.info("Log msg")
    logger.debug("Log msg")
    logger.error("Log msg")
    logger.info(f"Raw data before parsing: {data}")
    
    try:
        data = json.loads(data)
        # logger.debug(f"Parsed data: {data}")

        data = data[0]

        region = data["region"]
        road = data["road"]
        direction = data["direction"]
        ts = str(datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S"))
        vehicle_type = data["vehicle_type"]
        lane = data["lane"]
        speeding = data["speeding"]
        velocity = data["velocity"]

        logger.info(f"Data parsed successfully: {region} {type(region)}, {road} {type(road)}, {direction}, {ts}, {vehicle_type}, {lane}, {speeding}, {velocity}")
        
        # Return the Row with the correct data fields
        return Row(region, road, direction, ts, vehicle_type, lane, speeding, velocity)
    except Exception as e:
        logger.error(f"Failed to parse data: {data}. Error: {str(e)}")
        raise


def initialize_env() -> StreamExecutionEnvironment:
    """Makes stream execution environment initialization"""
    env = StreamExecutionEnvironment.get_execution_environment()

    # Get current directory
    root_dir_list = __file__.split("/")[:-2]
    root_dir = "/".join(root_dir_list)

    # Adding the jar to the flink streaming environment
    env.add_jars(
        f"file://{root_dir}/lib/flink-connector-jdbc-3.1.2-1.18.jar",
        f"file://{root_dir}/lib/postgresql-42.7.3.jar",
        f"file://{root_dir}/lib/flink-sql-connector-kafka-3.1.0-1.18.jar",
    )
    return env


def configure_source(server: str, earliest: bool = False) -> KafkaSource:
    """Makes Kafka source initialization"""
    properties = {
        "bootstrap.servers": server,
        "group.id": "traffic-data-consumer",
    }

    offset = KafkaOffsetsInitializer.latest()
    if earliest:
        offset = KafkaOffsetsInitializer.earliest()

    kafka_source = (
        KafkaSource.builder()
        .set_topics("Riyadh_King_Fahad_Road")
        .set_properties(properties)
        .set_starting_offsets(offset)
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )
    return kafka_source


def configure_postgre_sink(sql_dml: str, type_info: Types) -> JdbcSink:
    """Makes PostgreSQL sink initialization. Config params are set in this function."""
    return JdbcSink.sink(
        sql_dml,
        type_info,
        JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
        .with_url(f"jdbc:postgresql://{POSTGRES_HOST}/trafficdb")
        .with_driver_name("org.postgresql.Driver")
        .with_user_name("anotheruser")
        .with_password("anotherpassword")
        .build(),
        JdbcExecutionOptions.builder()
        .with_batch_interval_ms(200)
        .with_batch_size(200)
        .with_max_retries(5)
        .build(),
    )


def configure_kafka_sink(server: str, topic_name: str) -> KafkaSink:
    """Configure Kafka Sink for alerts"""
    return (
        KafkaSink.builder()
        .set_bootstrap_servers(server)
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
            .set_topic(topic_name)
            .set_value_serialization_schema(SimpleStringSchema())
            .build()
        )
        .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE)
        .build()
    )


def main() -> None:
    """Main flow controller"""

    # Initialize environment
    logger.info("Initializing environment for traffic data pipeline")
    env = initialize_env()

    # Define source and sinks
    logger.info("Configuring source and sinks")
    kafka_source = configure_source(KAFKA_HOST)
    sql_dml = (
        "INSERT INTO traffic_data (region, road, direction, ts, vehicle_type, lane, speeding, velocity) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    TYPE_INFO = Types.ROW(
        [
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
    jdbc_sink = configure_postgre_sink(sql_dml, TYPE_INFO)
    kafka_sink = configure_kafka_sink(KAFKA_HOST, "Riyadh_King_Fahad_Road")
    logger.info("Source and sinks initialized")

    # Create a DataStream from the Kafka source and assign watermarks
    data_stream = env.from_source(
        kafka_source, WatermarkStrategy.no_watermarks(), "Riyadh_King_Fahad_Road"
    )

    # Make transformations to the data stream
    transformed_data = data_stream.map(parse_data, output_type=TYPE_INFO)

    logger.info("Defined transformations to data stream")

    logger.info("Ready to sink data")
    transformed_data.add_sink(jdbc_sink)

    # Execute the Flink job
    env.execute("Flink Traffic Data Pipeline with PostgreSQL and Kafka Sink")


if __name__ == "__main__":
    main()
