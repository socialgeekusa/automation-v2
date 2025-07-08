import os
import threading
import time
import random

class WarmupManager:
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.active = False
        self.threads = []

    def start_all_warmup(self):
        """
        Start warmup for every device/account in config.
        """
        if self.active:
            print("Warmup already running")
            return
        self.active = True
        for device_id in self.config.accounts:
            t = threading.Thread(target=self._warmup_device_loop, args=(device_id,))
            t.start()
            self.threads.append(t)

    def stop_all_warmup(self):
        """
        Stop all warmup threads gracefully.
        """
        self.active = False
        # Threads check self.active and will exit naturally
        for t in self.threads:
            t.join()
        self.threads.clear()

    def _warmup_device_loop(self, device_id):
        """
        Loop performing warmup actions on a device until stopped.
        """
        while self.active:
            account_data = self.config.accounts.get(device_id, {})
            for platform in ["TikTok", "Instagram"]:
                platform_info = account_data.get(platform, {})
                active_account = platform_info.get("active")
                if active_account:
                    self.perform_warmup_actions(device_id, platform, active_account)
            # Wait 1 minute before next warmup cycle
            time.sleep(60)

    def perform_warmup_actions(self, device_id, platform, account):
        """
        Perform a set of actions based on warmup limits for platform.
        Logs each action to Logs/warmup_log.txt.
        """
        limits = self.config.settings.get("warmup_limits", {}).get(platform, {})
        min_delay = self.config.settings.get("min_delay", 5)
        max_delay = self.config.settings.get("max_delay", 15)
        log_path = os.path.join("Logs", "warmup_log.txt")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        # Likes
        like_min, like_max = limits.get("likes", [0, 0])
        for _ in range(random.randint(like_min, like_max)):
            print(f"Warmup like on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            with open(log_path, "a") as log:
                log.write(f"{time.asctime()}: Warmup LIKE {platform} {account} on {device_id}\n")

        # Follows
        follow_min, follow_max = limits.get("follows", [0, 0])
        for _ in range(random.randint(follow_min, follow_max)):
            print(f"Warmup follow on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            with open(log_path, "a") as log:
                log.write(f"{time.asctime()}: Warmup FOLLOW {platform} {account} on {device_id}\n")

        # Comments
        comment_min, comment_max = limits.get("comments", [0, 0])
        for _ in range(random.randint(comment_min, comment_max)):
            print(f"Warmup comment on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            with open(log_path, "a") as log:
                log.write(f"{time.asctime()}: Warmup COMMENT {platform} {account} on {device_id}\n")

        # Shares
        share_min, share_max = limits.get("shares", [0, 0])
        for _ in range(random.randint(share_min, share_max)):
            print(f"Warmup share on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            with open(log_path, "a") as log:
                log.write(f"{time.asctime()}: Warmup SHARE {platform} {account} on {device_id}\n")

        # Story Views
        view_min, view_max = limits.get("story_views", [0, 0])
        for _ in range(random.randint(view_min, view_max)):
            print(f"Warmup story view on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            with open(log_path, "a") as log:
                log.write(f"{time.asctime()}: Warmup STORY_VIEW {platform} {account} on {device_id}\n")

        # Story Likes
        like_story_min, like_story_max = limits.get("story_likes", [0, 0])
        for _ in range(random.randint(like_story_min, like_story_max)):
            print(f"Warmup story like on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            with open(log_path, "a") as log:
                log.write(f"{time.asctime()}: Warmup STORY_LIKE {platform} {account} on {device_id}\n")

        # Posts (if warmup day threshold reached)
        post_min, post_max = limits.get("posts", [0, 0])
        # Posting handled in PostManager; skip here

