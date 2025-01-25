#!/bin/bash

mkdir -p ./lib
echo "Running Custom Download Script"

curl -o ./lib/flink-connector-jdbc-3.1.2-1.18.jar https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.1.2-1.18/flink-connector-jdbc-3.1.2-1.18.jar
curl -o ./lib/postgresql-42.7.3.jar https://jdbc.postgresql.org/download/postgresql-42.7.3.jar
curl -o ./lib/flink-sql-connector-kafka-3.1.0-1.18.jar https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.1.0-1.18/flink-sql-connector-kafka-3.1.0-1.18.jar
curl -o ./lib/flink-doris-connector-1.18-24.0.0.jar https://repo.maven.apache.org/maven2/org/apache/doris/flink-doris-connector-1.18/24.0.0/flink-doris-connector-1.18-24.0.0.jar

echo "Libs downloaded successfully"
echo "Libs downloaded successfully"