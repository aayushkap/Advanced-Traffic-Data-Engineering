#!/bin/bash

# Wait for the JobManager to be ready
echo "Waiting for JobManager to be ready..."
until curl -s http://localhost:8081 | grep -q '<title>Apache Flink</title>'; do
    echo "JobManager not ready yet..."
    sleep 5
done

# Submit the Flink job
echo "Submitting Flink job..."
/opt/flink/bin/flink run -py /opt/flink/usr_jobs/doris_traffic_sink.py

# Keep the container running
tail -f /dev/null
