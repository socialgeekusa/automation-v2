import threading
import time
import random

class PostManager:
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.active = False
        self.thread = None

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

    def join(self, timeout=None):
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout)

    def _post_loop(self):
        while self.active:
            for device_id in self.config.accounts:
                for platform in ["TikTok", "Instagram"]:
                    accounts = self.config.accounts.get(device_id, {}).get(platform, {})
                    active_account = accounts.get("active")
                    if active_account:
                        self.post_draft(device_id, platform, active_account)
                        delay = random.uniform(900, 3600)  # Wait 15-60 mins between posts
                        time.sleep(delay)
            time.sleep(10)

    def post_draft(self, device_id, platform, account):
        # Placeholder for draft posting logic
        print(f"Posting draft on {platform} account {account} for device {device_id}")
