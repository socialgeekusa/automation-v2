import json
import os

class ConfigManager:
    def __init__(self):
        self.base_path = os.path.abspath(os.path.dirname(__file__))
        self.config_folder = os.path.join(self.base_path, "Config")
        os.makedirs(self.config_folder, exist_ok=True)

        self.devices_file = os.path.join(self.config_folder, "devices.json")
        self.accounts_file = os.path.join(self.config_folder, "accounts.json")
        self.settings_file = os.path.join(self.config_folder, "settings.json")
        self.account_settings_file = os.path.join(self.config_folder, "account_settings.json")

        self.devices = self.load_json(self.devices_file, default={})
        self.accounts = self.load_json(self.accounts_file, default={})
        self.account_settings = self.load_json(self.account_settings_file, default={})
        self.settings = self.load_json(self.settings_file, default={
            "fast_mode": False,
            "min_delay": 5,
            "max_delay": 15,
            "warmup_limits": {
                "TikTok": {"likes": [20,30], "follows": [5,10], "comments": [2,5], "shares": [1,3], "story_views": [50,100], "story_likes": [5,10], "posts": [0,0]},
                "Instagram": {"likes": [30,50], "follows": [10,15], "comments": [5,8], "shares": [3,5], "story_views": [100,200], "story_likes": [10,20], "posts": [0,1]}
            }
        })

    def load_json(self, filepath, default=None):
        if not os.path.exists(filepath):
            self.save_json(filepath, default if default is not None else {})
            return default if default is not None else {}
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return default if default is not None else {}

    def save_json(self, filepath, data):
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving {filepath}: {e}")

    def add_device(self, device_id, nickname=None):
        if device_id not in self.devices:
            self.devices[device_id] = nickname or device_id
            self.save_json(self.devices_file, self.devices)

    def remove_device(self, device_id):
        if device_id in self.devices:
            del self.devices[device_id]
            self.save_json(self.devices_file, self.devices)

    def update_nickname(self, device_id, nickname):
        self.devices[device_id] = nickname
        self.save_json(self.devices_file, self.devices)

    def add_account(self, device_id, platform, account_name):
        if device_id not in self.accounts:
            self.accounts[device_id] = {}
        if platform not in self.accounts[device_id]:
            self.accounts[device_id][platform] = {"accounts": [], "active": None}
        if account_name not in self.accounts[device_id][platform]["accounts"]:
            self.accounts[device_id][platform]["accounts"].append(account_name)
            if self.accounts[device_id][platform]["active"] is None:
                self.accounts[device_id][platform]["active"] = account_name
            self.save_json(self.accounts_file, self.accounts)

    def remove_account(self, device_id, platform, account_name):
        if device_id in self.accounts and platform in self.accounts[device_id]:
            accounts_list = self.accounts[device_id][platform]["accounts"]
            if account_name in accounts_list:
                accounts_list.remove(account_name)
                if self.accounts[device_id][platform]["active"] == account_name:
                    self.accounts[device_id][platform]["active"] = accounts_list[0] if accounts_list else None
                self.save_json(self.accounts_file, self.accounts)

    def set_active_account(self, device_id, platform, account_name):
        if device_id in self.accounts and platform in self.accounts[device_id]:
            if account_name in self.accounts[device_id][platform]["accounts"]:
                self.accounts[device_id][platform]["active"] = account_name
                self.save_json(self.accounts_file, self.accounts)

    def set_account_settings(self, username, settings):
        """Store per-account interaction settings."""
        self.account_settings[username] = settings
        self.save_json(self.account_settings_file, self.account_settings)

    def get_account_settings(self, username):
        return self.account_settings.get(username, {})
