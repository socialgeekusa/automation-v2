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
                        self.post_draft(device_id, platform, active_account)
                        delay = random.uniform(300, 900)
                        time.sleep(delay)
            time.sleep(10)

    def post_draft(self, device_id, platform, account):
        log_path = os.path.join("Logs", "post_log.txt")
        try:
            # Placeholder for draft posting logic
            print(f"Posting draft on {platform} account {account} for device {device_id}")
            with open(log_path, "a") as log:
                log.write(f"{time.asctime()}: SUCCESS post {platform} {account} on {device_id}\n")
        except Exception as e:
            with open(log_path, "a") as log:
                log.write(f"{time.asctime()}: FAIL post {platform} {account} on {device_id}: {e}\n")
