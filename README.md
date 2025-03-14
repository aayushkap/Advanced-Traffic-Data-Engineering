# Real-Time End-to-End Traffic Data Pipeline

- This project is a demonstration of a real-time end-to-end data pipeline that leverages the Apache ecosystem. The pipeline simulates, ingests, processes, and visualizes traffic data in real-time.

- The entire pipeline is designed for high throughput, scalability, and fault tolerance by leveraging built-in parallelism and concurrency features of Airflow, Kafka, Flink, and Doris.

## Components

1. **Airflow**  
   - An orchestration tool used for scheduling tasks.  
   - Simulates traffic data generation in real-time by dynamically creating DAG tasks for each road.  
   - Uses a Celery executor with each worker configured to run up to 4 tasks concurrently.  
   - The DAG is configured with `concurrency=4` and `max_active_runs=1`, ensuring that no more than 4 tasks run concurrently and that runs do not overlap.

2. **Kafka**  
   - An event streaming platform that ingests data and allows multiple consumers to process messages in parallel.  
   - Each road has its own Kafka topic, and each topic is created with **4 partitions**.  
   - This partitioning allows Kafka to distribute messages across multiple consumer threads, enabling parallel data consumption.

3. **Flink**  
   - A stream processing engine that consumes data from Kafka, cleans the data, and writes it to Doris.  
   - The Flink job is set with a default parallelism of 4, meaning that each operator (source, transformation, sink) runs 4 parallel tasks.  
   - The Job Manager coordinates the job, while the Task Manager—with 4 task slots—executes the parallel tasks.  
   - The Kafka source operator consumes data from all topics concurrently, processing messages from multiple partitions in parallel.

4. **Doris**  
   - A distributed SQL engine optimized for fast OLAP queries.  
   - Receives data via a JDBC sink that writes in batches.  
   - The sink is set up with 4 parallel tasks where each task buffers and writes its own batch (up to 1000 records per batch) independently, ensuring high throughput and fault tolerance.

5. **Dashboard**  
   - A real-time visualization dashboard for traffic data.  
   - Built with Apache ECharts and React (Vite), it provides various filters to customize the view.  
   - Accessible via a web browser at `localhost:5173`.

6. **Iceberg & MiniIO Integration**  
   - Each Kafka topic’s data is subscribed independently, and batching is applied before appending to Iceberg, which uses the MiniIO file system.


## Diagrams

- **Architecture Diagram**: 
![Architecture Diagram](/docs/Project_Architecture.png)

- **Parallelism Diagram**: 
![Parallelism Diagram](/docs/Parallelism_Diagram.png)

- **Dashboard UI**
![Dashboard UI](/docs/Dashboard_UI.png)

## How to Run

1. **Run Services:**  
   Build and run all services using Docker Compose:
   ```bash
   docker-compose up -d --build
    ```

2. **Submit Flink Job:**  
   Submit the Flink job that writes data to Doris with 4 parallel tasks:
   ```bash
   docker compose exec flink-jobmanager flink run -p 4 -py /opt/flink/usr_jobs/doris_traffic_sink.py
    ```

3. **Verify Airflow:**  
   Access the Airflow UI at `localhost:8080` and monitor the DAG execution.

4. **Access Dashboard:**
    Change the directory to `vehicle-dashboard` and run the following commands:
    ```bash
    npm install
    npm run dev
    ```
    Access the dashboard on your web browser at `localhost:5173`.


Feel free to reach out to me at: `aayushkap@outlook.com` if you have any issues/suggestions!
