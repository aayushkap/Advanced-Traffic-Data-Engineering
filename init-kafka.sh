#!/bin/bash
# Wait for Kafka to start
echo "Running Custom Script"
echo "Waiting for Kafka to start listening on localhost:9092"
sleep 10

# Create Kafka topics
# kafka-topics --create --topic sensors \
#   --bootstrap-server localhost:9092 \
#   --partitions 1 \
#   --replication-factor 1

# echo "Kafka topic created: sensors"

# kafka-topics --create --topic alerts \
#   --bootstrap-server localhost:9092 \
#   --partitions 1 \
#   --replication-factor 1

# echo "Kafka topic created: alerts"

# List Kafka topics
kafka-topics --bootstrap-server localhost:9092 --list
