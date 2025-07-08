import os
import time

LOG_DIR = os.path.join("Logs")

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "automation_log.txt")

def log(device_id, message):
    """Append a log entry with the device identifier."""
    timestamp = time.asctime()
    line = f"{timestamp}: {device_id}: {message}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)
