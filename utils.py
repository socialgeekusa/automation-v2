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
    """Return the device OS based on name or id heuristics.

    Devices whose name contains "iphone" (case-insensitive) or whose ID is a
    40-character string are treated as iPhones.  Additionally, if the device ID
    consists solely of digits and contains 20 or more characters, it is
    classified as an Android device.
    """

    name = device.get("name", "")
    dev_id = device.get("id", "")

    if "iphone" in name.lower() or len(dev_id) == 40:
        return "iPhone"

    if dev_id.isdigit() and len(dev_id) >= 20:
        return "Android"

    return "Android"
