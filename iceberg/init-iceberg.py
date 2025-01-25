import boto3
from botocore.exceptions import ClientError
from pyiceberg.catalog.sql import SqlCatalog
import pyarrow as pa

CATALOG = "iceberg-postgres" # iceberg-postgres
MINIO = "iceberg-minio" # iceberg-minio

# Create S3 bucket if it does not exist
s3_client = boto3.client(
    's3',
    endpoint_url=f"http://{MINIO}:9000",
    aws_access_key_id="minio",
    aws_secret_access_key="minio123"
)

bucket_name = "iceberg-data"
try:
    s3_client.head_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' already exists.")
except ClientError:
    print(f"Bucket '{bucket_name}' does not exist, creating it...")
    s3_client.create_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' created successfully.")

# Configure the Iceberg SQL Catalog
warehouse_path = "s3a://iceberg-data"
catalog = SqlCatalog(
    "default",
    **{
        "uri": f"postgresql://iceberg:iceberg@{CATALOG}:5432/iceberg",
        "warehouse": warehouse_path,
        "s3.endpoint": f"http://{MINIO}:9000",
        "s3.access-key-id": "minio",
        "s3.secret-access-key": "minio123",
    },
)

# Ensure the namespace exists
namespace = "default"
if not catalog._namespace_exists(namespace):
    print(f"Namespace '{namespace}' does not exist, creating it...")
    catalog.create_namespace(namespace)
print(f"Namespace '{namespace}' is ready!")

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

table_name = f"{namespace}.traffic-data"
try:
    table = catalog.create_table(table_name, schema=schema)
    print(f"Table '{table_name}' created successfully.")
except Exception as e:
    print(f"Unable to create table '{table_name}': {e}")
    if str(e) == f"Table {table_name} already exists":
        print(f"Table '{table_name}' already exists, dropping it...")
        catalog.drop_table(f"{table_name}") # Does not work
        table = catalog.create_table(table_name, schema=schema)
        print(f"Table '{table_name}' created successfully.")