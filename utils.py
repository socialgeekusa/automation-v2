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
    """Determine the device OS based on its ID prefix.

    Devices whose ID starts with ``0`` are considered iPhones while
    IDs beginning with ``Z`` are treated as Androids. Any other ID
    defaults to Android.
    """

    dev_id = device.get("id", "")

    if dev_id.startswith("0"):
        return "iPhone"

    if dev_id.startswith("Z"):
        return "Android"

    return "Android"
