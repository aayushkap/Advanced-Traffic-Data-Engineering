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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def initialize_env() -> StreamExecutionEnvironment:
    """Makes stream execution environment initialization"""
    env = StreamExecutionEnvironment.get_execution_environment()

    # current dir
    print(f"__file__: {__file__}")
    root_dir_list = __file__.split("/")[:-1]
    root_dir = "/".join(root_dir_list)
    print(f"Root dir list: {root_dir_list}")
    print(f"Root dir: {root_dir}")
    
    env.add_jars(
        f"file:///{root_dir}/lib/flink-connector-jdbc-3.1.2-1.18.jar",
        f"file:///{root_dir}/lib/postgresql-42.7.3.jar",
        f"file:///{root_dir}/lib/flink-sql-connector-kafka-3.1.0-1.18.jar",
        f"file:///{root_dir}/lib/mysql-connector-j-9.1.0.jar",
    )
    return env

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
        .with_batch_interval_ms(200)  # batch interval for flushing
        .with_batch_size(200)  # adjust batch size! Increase for higher ingestion rates (when kafka is faster) 
        .with_max_retries(5)
        .build(),
    )

    
def configure_source(server: str, earliest: bool = False) -> KafkaSource:
    """Makes kafka source initialization"""
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


def configure_kafka_sink(server: str, topic_name: str) -> KafkaSink:

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

    logger.info("Initializing environment for Doris Sink")
    env = initialize_env()
    
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

    doris_sink = configure_doris_sink(sql_dml, TYPE_INFO)
    kafka_sink = configure_kafka_sink(KAFKA_HOST, "alerts")
    logger.info("Source and sinks initialized")

    data_stream = env.from_source(
        kafka_source, WatermarkStrategy.no_watermarks(), "Kafka traffic topic"
    )

    transformed_data = data_stream.map(parse_data, output_type=TYPE_INFO)
    
    logger.info("Defined transformations to data stream")

    logger.info("Ready to sink data")
    transformed_data.add_sink(doris_sink)

    # execute flink job 
    env.execute("Flink Doris and Kafka Sink")


if __name__ == "__main__":
    print("Starting main")
    main()
