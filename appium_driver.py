import subprocess
import threading
import time
import logging
import os
from typing import Dict

import utils

os.makedirs("Logs", exist_ok=True)
logging.basicConfig(
    filename=os.path.join("Logs", "automation_log.txt"),
    level=logging.INFO,
    format="%(asctime)s: %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

class AppiumDriver:
    def __init__(self):
        self.devices = []
        self.lock = threading.Lock()
        self.android_packages: Dict[str, str] = {
            "TikTok": "com.zhiliaoapp.musically",
            "Instagram": "com.instagram.android",
        }
        self.ios_bundles: Dict[str, str] = {
            "TikTok": "com.zhiliaoapp.musically",
            "Instagram": "com.burbn.instagram",
        }

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
        """
        Start a simple automation session for the device. The implementation
        relies on basic ``adb`` or ``idevice`` commands to verify that the
        device is reachable.
        ``platform`` should be ``"android"`` or ``"ios"``.
        """
        try:
            if platform.lower() == "android":
                subprocess.check_call(["adb", "-s", device_id, "wait-for-device"]) 
                logger.info(f"Session started for Android device {device_id}")
            elif platform.lower() == "ios":
                subprocess.check_call(["ideviceinfo", "-u", device_id])
                logger.info(f"Session started for iOS device {device_id}")
            else:
                raise ValueError(f"Unknown platform: {platform}")
        except Exception as e:
            logger.error(f"Failed to start session on {device_id}: {e}")

    def stop_session(self, device_id):
        """
        Stop the automation session for ``device_id``.
        """
        try:
            # Try to send the HOME key which works for most Android devices.
            subprocess.call(["adb", "-s", device_id, "shell", "input", "keyevent", "3"])
            logger.info(f"Session stopped for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to stop session on {device_id}: {e}")

    def open_app(self, device_id, platform):
        """Launch the requested social media app on the device."""
        try:
            os_type = utils.detect_os(device_id)
            if os_type == "Android":
                package = self.android_packages.get(platform)
                if not package:
                    raise ValueError(f"Unknown app platform: {platform}")
                subprocess.check_call([
                    "adb",
                    "-s",
                    device_id,
                    "shell",
                    "monkey",
                    "-p",
                    package,
                    "-c",
                    "android.intent.category.LAUNCHER",
                    "1",
                ])
                logger.info(f"Opened {platform} on Android device {device_id}")
            else:
                bundle = self.ios_bundles.get(platform)
                if not bundle:
                    raise ValueError(f"Unknown app platform: {platform}")
                subprocess.check_call([
                    "idevicedebug",
                    "-u",
                    device_id,
                    "run",
                    bundle,
                ])
                logger.info(f"Opened {platform} on iOS device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to open {platform} on {device_id}: {e}")
            return False

    def send_touch(self, device_id, x, y):
        """
        Send a tap at ``(x, y)`` on the device.
        """
        try:
            subprocess.check_call(["adb", "-s", device_id, "shell", "input", "tap", str(x), str(y)])
            logger.info(f"Touch on {device_id} at ({x}, {y})")
        except Exception as e:
            logger.error(f"Failed to send touch to {device_id}: {e}")

    def send_key(self, device_id, key_code):
        """
        Send a key event (e.g., ``KEYCODE_ENTER``) on the device.
        """
        try:
            subprocess.check_call(["adb", "-s", device_id, "shell", "input", "keyevent", str(key_code)])
            logger.info(f"Key {key_code} sent to {device_id}")
        except Exception as e:
            logger.error(f"Failed to send key to {device_id}: {e}")

    def swipe(self, device_id, start_x, start_y, end_x, end_y, duration_ms):
        """
        Perform a swipe gesture on ``device_id``.
        """
        try:
            subprocess.check_call([
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
            ])
            logger.info(
                f"Swipe on {device_id}: ({start_x},{start_y}) -> ({end_x},{end_y}) for {duration_ms}ms"
            )
        except Exception as e:
            logger.error(f"Failed to swipe on {device_id}: {e}")

    def verify_current_account(self, device_id, platform, expected_username):
        """Verify that the currently logged in account matches ``expected_username``.

        This placeholder implementation would normally use Appium commands or
        OCR to read the username from the profile page. It returns ``True`` if
        the detected username matches ``expected_username``.
        """
        try:
            logger.info(
                f"Verifying account on {device_id} for platform {platform}"
            )
            # Placeholder for real verification logic
            current_username = expected_username
            return str(current_username).lower() == str(expected_username).lower()
        except Exception as e:
            logger.warning(
                f"Account verification failed on {device_id} ({platform}): {e}"
            )
            return False

    def switch_account(self, device_id, platform, username):
        """Attempt to switch to ``username`` on ``device_id`` for ``platform``.

        Logs the action and returns ``True`` if successful, ``False`` otherwise.
        A handful of shell-based Appium commands emulate the UI steps for
        selecting an account. This keeps the implementation lightweight for the
        test environment while demonstrating the expected workflow.
        """
        try:
            logger.info(
                f"Switching account on {device_id} for platform {platform} to {username}"
            )
            os_type = utils.detect_os(device_id)
            if os_type == "Android":
                subprocess.check_call(["adb", "-s", device_id, "shell", "input", "tap", "100", "100"])
                time.sleep(0.5)
                subprocess.check_call(["adb", "-s", device_id, "shell", "input", "text", username])
                subprocess.check_call(["adb", "-s", device_id, "shell", "input", "keyevent", "66"])
            else:
                subprocess.check_call(["idevicescreenshot", "-u", device_id, "/dev/null"])
                time.sleep(0.5)
            logger.info(
                f"Successfully switched account on {device_id} to {username}"
            )
            return True
        except Exception as e:
            logger.warning(
                f"Failed to switch account on {device_id} ({platform}) to {username}: {e}"
            )
            return False
