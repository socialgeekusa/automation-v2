import threading
import time
import random

class InteractionManager:
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.active = False
        self.thread = None

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

    def _interaction_loop(self):
        while self.active:
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
        # Placeholder for human-like interactions: scroll, like, comment, etc.
        actions = ["scroll", "like", "comment", "save", "share", "view_story", "like_story"]
        # choose a random subset of actions each loop
        for action in random.sample(actions, k=random.randint(1, 4)):
            print(f"Performing {action} on {platform} account {account} for device {device_id}")
            # here you’d call the driver’s methods, e.g. self.driver.swipe(...)
            time.sleep(random.uniform(
                self.config.settings.get("min_delay", 5),
                self.config.settings.get("max_delay", 15)
            ))
