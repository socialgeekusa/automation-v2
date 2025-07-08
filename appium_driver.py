import subprocess
import threading
import time
import os
import logging

class AppiumDriver:
    def __init__(self):
        self.devices = []
        self.lock = threading.Lock()
        self.sessions = {}
        log_dir = "Logs"
        os.makedirs(log_dir, exist_ok=True)
        self.logger = logging.getLogger("automation")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            handler = logging.FileHandler(os.path.join(log_dir, "automation_log.txt"))
            formatter = logging.Formatter("%(asctime)s: %(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def list_devices(self):
        """
        Returns a list of connected device IDs (Android & iOS).
        """
        devices = []
        try:
            # Android devices via ADB
            adb_output = subprocess.check_output(['adb', 'devices']).decode()
            for line in adb_output.splitlines()[1:]:
                if line.strip() and 'device' in line:
                    devices.append(line.split()[0])
        except Exception as e:
            print(f"Error listing Android devices: {e}")

        try:
            # iOS devices via idevice_id (from libimobiledevice)
            idevice_output = subprocess.check_output(['idevice_id', '-l']).decode()
            for line in idevice_output.splitlines():
                if line.strip():
                    devices.append(line.strip())
        except Exception as e:
            print(f"Error listing iOS devices: {e}")

        with self.lock:
            self.devices = devices
        return devices

    def start_session(self, device_id, platform):
        """Start a simple session using adb or idevice commands."""
        platform = platform.lower()
        try:
            if platform == "android":
                subprocess.check_output([
                    "adb",
                    "-s",
                    device_id,
                    "wait-for-device",
                ])
            elif platform == "ios":
                subprocess.check_output([
                    "ideviceinfo",
                    "-u",
                    device_id,
                ])
            else:
                raise ValueError("Unknown platform")
            self.sessions[device_id] = platform
            self.logger.info(f"SUCCESS start_session {platform} {device_id}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"FAIL start_session {platform} {device_id}: {e.output.decode().strip()}"
            )
        except Exception as e:
            self.logger.error(f"FAIL start_session {platform} {device_id}: {e}")
        return False

    def stop_session(self, device_id):
        """Stop a session by issuing basic device commands."""
        platform = self.sessions.get(device_id)
        if not platform:
            self.logger.warning(f"stop_session: no session for {device_id}")
            return False
        try:
            if platform == "android":
                subprocess.check_output(
                    ["adb", "-s", device_id, "shell", "input", "keyevent", "3"]
                )
            else:
                subprocess.check_output(
                    ["idevicediagnostics", "restart", "-u", device_id]
                )
            self.sessions.pop(device_id, None)
            self.logger.info(f"SUCCESS stop_session {platform} {device_id}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"FAIL stop_session {platform} {device_id}: {e.output.decode().strip()}"
            )
        except Exception as e:
            self.logger.error(f"FAIL stop_session {platform} {device_id}: {e}")
        return False

    def send_touch(self, device_id, x, y):
        """Send a simple touch event via adb/idevice."""
        platform = self.sessions.get(device_id, "android")
        try:
            if platform == "android":
                subprocess.check_output(
                    ["adb", "-s", device_id, "shell", "input", "tap", str(x), str(y)]
                )
            else:
                subprocess.check_output(
                    [
                        "idevicedebug",
                        "-u",
                        device_id,
                        "tap",
                        str(x),
                        str(y),
                    ]
                )
            self.logger.info(f"SUCCESS touch {device_id} {x},{y}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"FAIL touch {device_id} {x},{y}: {e.output.decode().strip()}"
            )
        except Exception as e:
            self.logger.error(f"FAIL touch {device_id} {x},{y}: {e}")
        return False

    def send_key(self, device_id, key_code):
        """Send a key event via adb/idevice."""
        platform = self.sessions.get(device_id, "android")
        try:
            if platform == "android":
                subprocess.check_output(
                    ["adb", "-s", device_id, "shell", "input", "keyevent", str(key_code)]
                )
            else:
                subprocess.check_output(
                    ["idevicedebug", "-u", device_id, "key", str(key_code)]
                )
            self.logger.info(f"SUCCESS key {device_id} {key_code}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"FAIL key {device_id} {key_code}: {e.output.decode().strip()}"
            )
        except Exception as e:
            self.logger.error(f"FAIL key {device_id} {key_code}: {e}")
        return False

    def swipe(self, device_id, start_x, start_y, end_x, end_y, duration_ms):
        """Perform a swipe gesture via adb/idevice."""
        platform = self.sessions.get(device_id, "android")
        try:
            if platform == "android":
                subprocess.check_output(
                    [
                        "adb",
                        "-s",
                        device_id,
                        "shell",
                        "input",
                        "swipe",
                        str(start_x),
                        str(start_y),
                        str(end_x),
                        str(end_y),
                        str(duration_ms),
                    ]
                )
            else:
                subprocess.check_output(
                    [
                        "idevicedebug",
                        "-u",
                        device_id,
                        "swipe",
                        str(start_x),
                        str(start_y),
                        str(end_x),
                        str(end_y),
                        str(duration_ms),
                    ]
                )
            self.logger.info(
                f"SUCCESS swipe {device_id} {start_x},{start_y}->{end_x},{end_y} in {duration_ms}ms"
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"FAIL swipe {device_id}: {e.output.decode().strip()}"
            )
        except Exception as e:
            self.logger.error(f"FAIL swipe {device_id}: {e}")
        return False
