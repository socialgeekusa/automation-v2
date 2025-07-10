import threading
import time
import random
import os

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
            return

        settings_override = self.config.get_account_settings(account)
        min_delay = settings_override.get("min_delay", self.config.settings.get("min_delay", 5))
        max_delay = settings_override.get("max_delay", self.config.settings.get("max_delay", 15))

        global_limits = self.config.settings.get("interaction_limits", {}).get(platform, {})
        account_limits = settings_override.get("interaction_limits", {}).get(platform, {})
        action_min, action_max = account_limits.get(
            "actions_per_cycle",
            global_limits.get("actions_per_cycle", [1, 4]),
        )
        action_count = random.randint(action_min, action_max)

        # choose a random subset of actions each loop
        for action in random.sample(actions, k=min(action_count, len(actions))):
            print(f"Performing {action} on {platform} account {account} for device {device_id}")
            line = f"[{device_id}] {time.asctime()}: {action.upper()} {platform} {account} on {device_id}\n"
            with open(log_path, "a") as log:
                log.write(line)
            self.config.update_last_activity(device_id, platform)
            # here you’d call the driver’s methods, e.g. self.driver.swipe(...)
            time.sleep(random.uniform(min_delay, max_delay))
