import os
import threading
import time
import json
import random

class WarmupManager:
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.active = False
        self.threads = []
        self.progress_file = os.path.join("Config", "warmup_progress.json")
        self.progress = self._load_progress()
        self.total_days = 7
        self.paused = False

    def _load_progress(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_progress(self):
        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        with open(self.progress_file, "w") as f:
            json.dump(self.progress, f, indent=4)

    def get_progress(self, device_id=None):
        """Return warmup progress for a specific device or all devices."""
        # Reload progress from disk in case other threads updated it
        self.progress = self._load_progress()
        if device_id is None:
            return dict(self.progress)
        return self.progress.get(device_id, 0)

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
        self.paused = False
        # Threads check self.active and will exit naturally
        for t in self.threads:
            t.join()
        self.threads.clear()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def _warmup_device_loop(self, device_id):
        """
        Loop performing warmup actions on a device until stopped.
        """
        day = self.progress.get(device_id, 0)
        while self.active and day < self.total_days:
            if self.paused:
                time.sleep(1)
                continue
            account_data = self.config.accounts.get(device_id, {})
            for platform in ["TikTok", "Instagram"]:
                platform_info = account_data.get(platform, {})
                active_account = platform_info.get("active")
                if active_account:
                    self.perform_warmup_actions(device_id, platform, active_account)
            # Wait 1 minute before next warmup cycle
            day += 1
            self.progress[device_id] = day
            self._save_progress()
            time.sleep(60)

    def perform_warmup_actions(self, device_id, platform, account):
        """
        Perform a set of actions based on warmup limits for platform.
        Logs each action to Logs/warmup_log.txt.
        """
        limits = self.config.settings.get("warmup_limits", {}).get(platform, {})
        min_delay = self.config.settings.get("min_delay", 5)
        max_delay = self.config.settings.get("max_delay", 15)
        log_dir = os.path.join("Logs")
        log_path = os.path.join(log_dir, "warmup_log.txt")
        automation_log = os.path.join(log_dir, "automation_log.txt")
        os.makedirs(log_dir, exist_ok=True)

        def append_logs(message: str):
            with open(log_path, "a") as log:
                log.write(message)
            with open(automation_log, "a") as auto_log:
                auto_log.write(message)

        # Likes
        like_min, like_max = limits.get("likes", [0, 0])
        for _ in range(like_min):
            print(f"Warmup like on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"{time.asctime()}: Warmup LIKE {platform} {account} on {device_id}\n"
            append_logs(line)

        # Follows
        follow_min, follow_max = limits.get("follows", [0, 0])
        for _ in range(follow_min):
            print(f"Warmup follow on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"{time.asctime()}: Warmup FOLLOW {platform} {account} on {device_id}\n"
            append_logs(line)

        # Comments
        comment_min, comment_max = limits.get("comments", [0, 0])
        for _ in range(comment_min):
            print(f"Warmup comment on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"{time.asctime()}: Warmup COMMENT {platform} {account} on {device_id}\n"
            append_logs(line)

        # Shares
        share_min, share_max = limits.get("shares", [0, 0])
        for _ in range(share_min):
            print(f"Warmup share on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"{time.asctime()}: Warmup SHARE {platform} {account} on {device_id}\n"
            append_logs(line)

        # Story Views
        view_min, view_max = limits.get("story_views", [0, 0])
        for _ in range(view_min):
            print(f"Warmup story view on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"{time.asctime()}: Warmup STORY_VIEW {platform} {account} on {device_id}\n"
            append_logs(line)

        # Story Likes
        like_story_min, like_story_max = limits.get("story_likes", [0, 0])
        for _ in range(like_story_min):
            print(f"Warmup story like on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"{time.asctime()}: Warmup STORY_LIKE {platform} {account} on {device_id}\n"
            append_logs(line)

        # Posts (if warmup day threshold reached)
        post_min, post_max = limits.get("posts", [0, 0])
        # Posting handled in PostManager; skip here

