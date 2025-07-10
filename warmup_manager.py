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
        # progress is stored per username to allow multiple accounts per device
        # using independent warmup schedules
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

    def get_progress(self, username=None):
        """Return warmup progress for a specific account or all accounts."""
        # Reload progress from disk in case other threads updated it
        self.progress = self._load_progress()
        if username is None:
            return dict(self.progress)
        return self.progress.get(username, 0)

    def is_warmup_active(self, username: str) -> bool:
        """Check if warmup should still run for the given username."""
        return self.get_progress(username) < self.total_days

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
        """Loop performing warmup actions on a device until stopped."""
        while self.active:
            if self.paused:
                time.sleep(1)
                continue

            account_data = self.config.accounts.get(device_id, {})
            all_done = True
            for platform in ["TikTok", "Instagram"]:
                platform_info = account_data.get(platform, {})
                active_account = platform_info.get("active")
                if not active_account:
                    continue
                day = self.progress.get(active_account, 0)
                if day < self.total_days:
                    all_done = False
                    self.perform_warmup_actions(device_id, platform, active_account)
                    self.progress[active_account] = day + 1
                    self._save_progress()

            if all_done:
                break
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

        if not self.driver.verify_current_account(device_id, platform, account):
            warning = (
                f"[{device_id}] {time.asctime()}: WARNING account mismatch for {platform} {account} on {device_id}\n"
            )
            with open(automation_log, "a") as auto_log:
                auto_log.write(warning)
            print(warning.strip())

            switched = self.driver.switch_account(device_id, platform, account)
            result = "SUCCESS" if switched else "FAIL"
            switch_line = (
                f"[{device_id}] {time.asctime()}: SWITCH {result} {platform} {account} on {device_id}\n"
            )
            with open(automation_log, "a") as auto_log:
                auto_log.write(switch_line)
            print(switch_line.strip())

            if not switched:
                return

        account_settings = self.config.get_account_settings(account)
        min_delay = account_settings.get("min_delay", min_delay)
        max_delay = account_settings.get("max_delay", max_delay)

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
            line = f"[{device_id}] {time.asctime()}: Warmup LIKE {platform} {account} on {device_id}\n"
            append_logs(line)

        # Follows
        follow_min, follow_max = limits.get("follows", [0, 0])
        for _ in range(follow_min):
            print(f"Warmup follow on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"[{device_id}] {time.asctime()}: Warmup FOLLOW {platform} {account} on {device_id}\n"
            append_logs(line)

        # Comments
        comment_min, comment_max = limits.get("comments", [0, 0])
        for _ in range(comment_min):
            print(f"Warmup comment on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"[{device_id}] {time.asctime()}: Warmup COMMENT {platform} {account} on {device_id}\n"
            append_logs(line)

        # Shares
        share_min, share_max = limits.get("shares", [0, 0])
        for _ in range(share_min):
            print(f"Warmup share on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"[{device_id}] {time.asctime()}: Warmup SHARE {platform} {account} on {device_id}\n"
            append_logs(line)

        # Story Views
        view_min, view_max = limits.get("story_views", [0, 0])
        for _ in range(view_min):
            print(f"Warmup story view on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"[{device_id}] {time.asctime()}: Warmup STORY_VIEW {platform} {account} on {device_id}\n"
            append_logs(line)

        # Story Likes
        like_story_min, like_story_max = limits.get("story_likes", [0, 0])
        for _ in range(like_story_min):
            print(f"Warmup story like on {platform} account {account} for device {device_id}")
            time.sleep(random.uniform(min_delay, max_delay))
            line = f"[{device_id}] {time.asctime()}: Warmup STORY_LIKE {platform} {account} on {device_id}\n"
            append_logs(line)

        # Posts (if warmup day threshold reached)
        post_min, post_max = limits.get("posts", [0, 0])
        # Posting handled in PostManager; skip here

