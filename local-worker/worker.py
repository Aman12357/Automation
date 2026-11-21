import os, socket, time
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
WORKER_ID = os.getenv("WORKER_ID", socket.gethostname().lower())
INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "60"))

def main():
    print(f"GTA Shorts worker {WORKER_ID} -> {API_BASE_URL}")
    while True:
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/workers/heartbeat",
                json={"worker_id": WORKER_ID, "hostname": socket.gethostname(), "version": "0.1.0"},
                timeout=10,
            )
            response.raise_for_status()
            print("Heartbeat accepted:", response.json())
        except requests.RequestException as exc:
            print("API unavailable; will retry:", exc)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
