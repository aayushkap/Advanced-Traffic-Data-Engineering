import os
import uuid
from datetime import datetime, timezone
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, DataTypes, TableDescriptor
from pyflink.common.typeinfo import Types
from pyflink.datastream.functions import SourceFunction

# Initialize environment
env = StreamExecutionEnvironment.get_execution_environment()
table_env = StreamTableEnvironment.create(env)


# Add Iceberg Flink runtime JAR

# Check if the JAR is available
if not os.path.exists("pyflink/usr_jobs/lib/iceberg-flink-runtime-1.18-1.6.1.jar"):
    raise FileNotFoundError("Iceberg Flink runtime JAR not found!")


iceberg_flink_runtime_jar = os.path.join(os.getcwd(), "pyflink/usr_jobs/lib/iceberg-flink-runtime-1.18-1.6.1.jar")
print(f"Adding Iceberg Flink runtime JAR: {iceberg_flink_runtime_jar}")

# Add HDFS and Hadoop Common JARs
hadoop_hdfs_jar = os.path.join(os.getcwd(), "pyflink/usr_jobs/lib/hadoop-hdfs-3.3.6.jar")
hadoop_common_jar = os.path.join(os.getcwd(), "pyflink/usr_jobs/lib/hadoop-common-3.3.6.jar")
hadoop_client_jar = os.path.join(os.getcwd(), "pyflink/usr_jobs/lib/hadoop-client-3.3.6.jar")

if not os.path.exists(hadoop_hdfs_jar) or not os.path.exists(hadoop_common_jar) or not os.path.exists(hadoop_client_jar):
    raise FileNotFoundError("Required Hadoop HDFS or Common JARs not found!")

print(f"Adding Hadoop HDFS JAR: {hadoop_hdfs_jar}")
print(f"Adding Hadoop Common JAR: {hadoop_common_jar}")
print(f"Adding Hadoop Client JAR: {hadoop_client_jar}")

env.add_jars(
    f"file://{iceberg_flink_runtime_jar}",
    f"file://{hadoop_hdfs_jar}",
    f"file://{hadoop_common_jar}",
    f"file://{hadoop_client_jar}"
)


table_env.get_config().get_configuration().set_string(
    "pipeline.jars",
    ",".join([
        f"file://{iceberg_flink_runtime_jar}",
        f"file://{hadoop_hdfs_jar}",
        f"file://{hadoop_common_jar}",
        f"file://{hadoop_client_jar}"
    ])
)

factories = table_env.list_catalogs()
print(f"Available catalog factories: {factories}")


# Configure Iceberg SQL catalog
warehouse_path = "s3a://iceberg-data"
table_env.execute_sql(f"""
    CREATE CATALOG my_minio_catalog WITH (
        'type' = 'iceberg',
        'catalog-type' = 'jdbc',
        'uri' = 'jdbc:postgresql://localhost:5432/iceberg',
        'warehouse' = '{warehouse_path}',
        's3.endpoint' = 'http://localhost:9000',
        's3.access-key-id' = 'minio',
        's3.secret-access-key' = 'minio123',
        'property-version' = '1'
    )
""")

table_env.use_catalog("my_minio_catalog")
print("-> Catalog configured successfully!")

# Define schema for incoming data
schema = DataTypes.ROW([
    DataTypes.FIELD("message_id", DataTypes.STRING()),
    DataTypes.FIELD("sensor_id", DataTypes.STRING()),
    DataTypes.FIELD("temperature", DataTypes.DOUBLE()),
    DataTypes.FIELD("pressure", DataTypes.DOUBLE()),
    DataTypes.FIELD("vibration", DataTypes.DOUBLE()),
    DataTypes.FIELD("timestamp", DataTypes.STRING())
])

# Create an Iceberg table
table_env.execute_sql(f"""
    CREATE TABLE IF NOT EXISTS default.sensor_data (
        message_id STRING,
        sensor_id STRING,
        temperature DOUBLE,
        pressure DOUBLE,
        vibration DOUBLE,
        `timestamp` STRING
    ) PARTITIONED BY (`timestamp`)
    WITH (
        'connector' = 'iceberg',
        'format' = 'parquet'
    )
""")
print("Iceberg table created successfully!")

# Simulate incoming data using a SourceFunction
class SensorSource(SourceFunction):
    def run(self, ctx):
        import random
        while True:
            ctx.collect((
                uuid.uuid4().hex,
                str(random.randint(1, 100)),
                random.uniform(20.0, 30.0),
                random.uniform(1.0, 2.0),
                random.uniform(0.0, 1.0),
                datetime.now(timezone.utc).isoformat()
            ))

    def cancel(self):
        pass

# Create a DataStream from the SourceFunction
data_stream = env.add_source(SensorSource(), type_info=Types.TUPLE([
    Types.STRING(),  # message_id
    Types.STRING(),  # sensor_id
    Types.DOUBLE(),  # temperature
    Types.DOUBLE(),  # pressure
    Types.DOUBLE(),  # vibration
    Types.STRING()   # timestamp
]))

# Convert DataStream to Table
table = table_env.from_data_stream(data_stream, schema)

# Write to Iceberg table
table.execute_insert("default.sensor_data")

# Execute the Flink job
env.execute("Flink to Iceberg Streaming")
