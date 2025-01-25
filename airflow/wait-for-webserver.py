import time
import requests

WEBSERVER_URL = "http://webserver:8080/health"
RETRY_INTERVAL = 5  # seconds
MAX_RETRIES = 60  # wait for 5 minutes max

def wait_for_webserver():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(WEBSERVER_URL, timeout=5)
            if response.status_code == 200:
                print("Webserver is ready!")
                return
            else:
                print(f"Webserver not ready, status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error connecting to webserver: {e}")
        retries += 1
        time.sleep(RETRY_INTERVAL)
    raise Exception("Webserver did not become ready in time!")

if __name__ == "__main__":
    wait_for_webserver()
