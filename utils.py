import time
from datetime import datetime


def detect_os(device_id: str) -> str:
    """Simple OS detection based on device id length."""
    return "iOS" if len(device_id) == 40 else "Android"


def timestamp_now() -> float:
    return time.time()


def format_last_activity(ts: float | None) -> str:
    if not ts:
        return "--"
    dt = datetime.fromtimestamp(ts)
    label = dt.strftime("%H:%M:%S")
    if dt.date() == datetime.today().date():
        return f"{label} (Today)"
    return f"{label} ({dt.date()})"


def detect_device_os(device):
    if "iPhone" in device.get('name', ''):
        return "iPhone"
    else:
        return "Android"
