import threading
import time
import random
import os

class PostManager:
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.active = False
        self.thread = None
        self.paused = False

    def run(self):
        if self.active:
            print("PostManager already running")
            return
        self.active = True
        self.thread = threading.Thread(target=self._post_loop)
        self.thread.start()

    def stop(self):
        self.active = False
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def _calculate_delay(self, account=None):
        """Calculate sleep delay between posts respecting fast mode and account overrides."""
        min_delay = self.config.settings.get("min_delay", 5)
        max_delay = self.config.settings.get("max_delay", 15)
        if account:
            overrides = self.config.get_account_settings(account)
            min_delay = overrides.get("min_delay", min_delay)
            max_delay = overrides.get("max_delay", max_delay)
        factor = 0.2 if self.config.settings.get("fast_mode") else 1.0
        min_delay *= 60 * factor
        max_delay *= 60 * factor
        return random.uniform(min_delay, max_delay)

    def _post_loop(self):
        log_path = os.path.join("Logs", "post_log.txt")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        while self.active:
            if self.paused:
                time.sleep(1)
                continue
            for device_id in self.config.accounts:
                for platform in ["TikTok", "Instagram"]:
                    accounts = self.config.accounts.get(device_id, {}).get(platform, {})
                    active_account = accounts.get("active")
                    if active_account:
                        self.driver.start_session(device_id, platform)
                        self.driver.open_app(device_id, platform)
                        self.post_draft(device_id, platform, active_account)
                        delay = self._calculate_delay(active_account)
                        time.sleep(delay)
            time.sleep(10)

    def post_draft(self, device_id, platform, account):
        log_dir = os.path.join("Logs")
        log_path = os.path.join(log_dir, "post_log.txt")
        automation_log = os.path.join(log_dir, "automation_log.txt")
        os.makedirs(log_dir, exist_ok=True)

        if not self.driver.verify_current_account(device_id, platform, account):
            warning = f"[{device_id}] {time.asctime()}: WARNING account mismatch for {platform} {account} on {device_id}\n"
            with open(automation_log, "a") as auto_log:
                auto_log.write(warning)
            print(warning.strip())
            switched = self.driver.switch_account(device_id, platform, account)
            result = "SUCCESS" if switched else "FAIL"
            switch_line = f"[{device_id}] {time.asctime()}: SWITCH {result} {platform} {account} on {device_id}\n"
            with open(automation_log, "a") as auto_log:
                auto_log.write(switch_line)
            print(switch_line.strip())
            if not switched:
                return
        try:
            # Placeholder for draft posting logic
            print(f"Posting draft on {platform} account {account} for device {device_id}")
            line = f"[{device_id}] {time.asctime()}: SUCCESS post {platform} {account} on {device_id}\n"
            with open(log_path, "a") as log:
                log.write(line)
            with open(automation_log, "a") as auto_log:
                auto_log.write(line)
        except Exception as e:
            line = f"[{device_id}] {time.asctime()}: FAIL post {platform} {account} on {device_id}: {e}\n"
            with open(log_path, "a") as log:
                log.write(line)
            with open(automation_log, "a") as auto_log:
                auto_log.write(line)
