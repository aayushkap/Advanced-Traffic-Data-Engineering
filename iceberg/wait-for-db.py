import time
import requests
from requests.auth import HTTPBasicAuth
import json

# MinIO server configuration
MINIO_HEALTH_URL = "http://iceberg-minio:9001/minio/health/live"
MINIO_ACCESS_KEY = "minio"
MINIO_SECRET_KEY = "minio123"

# Retry configuration
RETRY_COUNT = 10
WAIT_SECONDS = 5

def check_minio_availability():
    try:
        # Send a GET request to MinIO's health endpoint
        response = requests.get(
            MINIO_HEALTH_URL,
            auth=HTTPBasicAuth(MINIO_ACCESS_KEY, MINIO_SECRET_KEY),
            timeout=5
        )
        # Check if the response status code is 200 (healthy)
        if response.status_code == 200:
            print("MinIO server is healthy.")
            return True
        else:
            print(f"MinIO server responded with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to MinIO server: {e}")
    return False

def main():
    print("Checking MinIO server availability...")
    for attempt in range(RETRY_COUNT):
        print(f"Attempt {attempt + 1} of {RETRY_COUNT}...")
        if check_minio_availability():
            print("MinIO server is available. Exiting gracefully.")
            return
        print(f"MinIO server not available. Waiting {WAIT_SECONDS} seconds before retrying...")
        time.sleep(WAIT_SECONDS)
    
    print("MinIO server is not available after multiple attempts. Exiting with failure.")
    exit(1)

if __name__ == "__main__":
    main()
