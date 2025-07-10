import threading
import time
import random
import os

# Default gesture coordinates used for Appium interactions. These values can
# be overridden via ``config.settings['gesture_coords']`` if desired.
DEFAULT_GESTURES = {
    "scroll": {"start": (500, 1500), "end": (500, 500), "duration": 800},
    "like": {"pos": (540, 1700)},
    "comment": {"pos": (640, 1700)},
    "save": {"pos": (740, 1700)},
    "share": {"pos": (840, 1700)},
    "view_story": {"pos": (100, 300)},
    "like_story": {"pos": (540, 300)},
}

class InteractionManager:
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.active = False
        self.thread = None
        self.paused = False

    def run(self):
        if self.active:
            print("InteractionManager already running")
            return
        self.active = True
        self.thread = threading.Thread(target=self._interaction_loop)
        self.thread.start()

    def stop(self):
        self.active = False
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def _interaction_loop(self):
        while self.active:
            if self.paused:
                time.sleep(1)
                continue
            for device_id, details in self.config.accounts.items():
                for platform in ["TikTok", "Instagram"]:
                    platform_info = details.get(platform, {})
                    active_account = platform_info.get("active")
                    if active_account:
                        self.driver.start_session(device_id, platform)
                        self.driver.open_app(device_id, platform)
                        self.perform_interactions(device_id, platform, active_account)
                        # random delay between each account’s interactions
                        delay = random.uniform(
                            self.config.settings.get("min_delay", 5),
                            self.config.settings.get("max_delay", 15)
                        )
                        time.sleep(delay)
            time.sleep(10)

    def perform_interactions(self, device_id, platform, account):
        """Perform a subset of interactions and log each action."""
        actions = [
            "scroll",
            "like",
            "comment",
            "save",
            "share",
            "view_story",
            "like_story",
        ]

        log_dir = os.path.join("Logs")
        log_path = os.path.join(log_dir, "automation_log.txt")
        os.makedirs(log_dir, exist_ok=True)

        if not self.driver.verify_current_account(device_id, platform, account):
            warning = f"[{device_id}] {time.asctime()}: WARNING account mismatch for {platform} {account} on {device_id}\n"
            with open(log_path, "a") as log:
                log.write(warning)
            print(warning.strip())
            switched = self.driver.switch_account(device_id, platform, account)
            result = "SUCCESS" if switched else "FAIL"
            switch_line = f"[{device_id}] {time.asctime()}: SWITCH {result} {platform} {account} on {device_id}\n"
            with open(log_path, "a") as log:
                log.write(switch_line)
            print(switch_line.strip())
            if not switched:
                return

        settings_override = self.config.get_account_settings(account)
        min_delay = settings_override.get("min_delay", self.config.settings.get("min_delay", 5))
        max_delay = settings_override.get("max_delay", self.config.settings.get("max_delay", 15))

        gestures = DEFAULT_GESTURES.copy()
        gestures.update(self.config.settings.get("gesture_coords", {}))

        # choose a random subset of actions each loop
        for action in random.sample(actions, k=random.randint(1, 4)):
            print(
                f"Performing {action} on {platform} account {account} for device {device_id}"
            )
            line = (
                f"[{device_id}] {time.asctime()}: {action.upper()} {platform} {account} on {device_id}\n"
            )
            with open(log_path, "a") as log:
                log.write(line)
            self.config.update_last_activity(device_id, platform)

            coords = gestures.get(action, {})
            if action == "scroll":
                start = coords.get("start", (500, 1500))
                end = coords.get("end", (500, 500))
                duration = coords.get("duration", 800)
                self.driver.swipe(device_id, start[0], start[1], end[0], end[1], duration)
            elif action == "comment":
                pos = coords.get("pos", (640, 1700))
                self.driver.send_touch(device_id, pos[0], pos[1])
                # send enter key as placeholder for submitting comment
                self.driver.send_key(device_id, 66)
            else:
                pos = coords.get("pos", (540, 1700))
                self.driver.send_touch(device_id, pos[0], pos[1])

            time.sleep(random.uniform(min_delay, max_delay))
