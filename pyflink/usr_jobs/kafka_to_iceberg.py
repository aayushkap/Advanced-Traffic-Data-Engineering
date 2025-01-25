from pyflink.table import EnvironmentSettings, TableEnvironment

# Create TableEnvironment
env_settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
table_env = TableEnvironment.create(env_settings)

print("Table Environment Created")

# Define Kafka Source Table
table_env.execute_sql("""
CREATE TABLE kafka_source (
    message_id STRING,
    sensor_id INT,
    message STRING,
    `timestamp` TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'sensors',
    'properties.bootstrap.servers' = 'kafka:19092',
    'properties.group.id' = 'iot-sensors',
    'format' = 'json',
    'scan.startup.mode' = 'earliest-offset'
)
""")

print("Kafka Source Table Created")

# Define Iceberg Sink Table
table_env.execute_sql("""
CREATE TABLE iceberg_sink (
    message_id STRING,
    sensor_id INT,
    message STRING,
    `timestamp` TIMESTAMP(3)
) WITH (
    'connector' = 'iceberg',
    'catalog-name' = 'default',
    'catalog-database' = 'default',
    'catalog-table' = 'raw_sensors_data',
    'write.format.default' = 'parquet',
    'path' = 's3://warehouse/raw_sensors_data/'
)
""")

print("Iceberg Sink Table Created")

# Insert Data from Kafka to Iceberg
table_env.execute_sql("INSERT INTO iceberg_sink SELECT * FROM kafka_source")

print("Data Inserted from Kafka to Iceberg")
