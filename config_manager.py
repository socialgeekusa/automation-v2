import json
import os
from typing import Dict, Optional
import utils

class ConfigManager:
    def __init__(self):
        self.base_path = os.path.abspath(os.path.dirname(__file__))
        self.config_folder = os.path.join(self.base_path, "Config")
        os.makedirs(self.config_folder, exist_ok=True)

        self.devices_file = os.path.join(self.config_folder, "devices.json")
        self.accounts_file = os.path.join(self.config_folder, "accounts.json")
        self.settings_file = os.path.join(self.config_folder, "settings.json")
        self.account_settings_file = os.path.join(self.config_folder, "account_settings.json")
        self.state_file = os.path.join(self.config_folder, "device_state.json")

        self.devices_data = self.load_json(self.devices_file, default={"devices": []})
        if isinstance(self.devices_data, dict) and "devices" in self.devices_data:
            self.devices_info = self.devices_data.get("devices", [])
        else:
            # backward compatibility with old dict format
            self.devices_info = [
                {"id": d_id, "name": name, "accounts": 0}
                for d_id, name in (self.devices_data or {}).items()
            ]
        self.devices = {d["id"]: d.get("name", d["id"]) for d in self.devices_info}
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
        self.device_states: Dict[str, Dict] = self.load_json(self.state_file, default={})
        for dev in self.devices_info:
            dev["accounts"] = self._get_account_count(dev["id"])
            counts = self.get_account_counts(dev["id"])
            dev["tiktok"] = counts["TikTok"]
            dev["instagram"] = counts["Instagram"]
        self._save_devices_info()

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

    def _save_devices_info(self):
        self.save_json(self.devices_file, {"devices": self.devices_info})

    def _save_states(self):
        self.save_json(self.state_file, self.device_states)

    def _get_account_count(self, device_id):
        count = 0
        if device_id in self.accounts:
            for platform_data in self.accounts[device_id].values():
                count += len(platform_data.get("accounts", []))
        return count

    def get_account_counts(self, device_id) -> Dict[str, int]:
        return {
            "TikTok": len(self.accounts.get(device_id, {}).get("TikTok", {}).get("accounts", [])),
            "Instagram": len(self.accounts.get(device_id, {}).get("Instagram", {}).get("accounts", [])),
        }

    def update_device_accounts(self, device_id):
        for dev in self.devices_info:
            if dev["id"] == device_id:
                dev["accounts"] = self._get_account_count(device_id)
                counts = self.get_account_counts(device_id)
                dev["tiktok"] = counts["TikTok"]
                dev["instagram"] = counts["Instagram"]
                self._save_devices_info()
                break

    def set_device_status(self, device_id: str, status: str):
        state = self.device_states.setdefault(device_id, {})
        state["status"] = status
        self._save_states()

    def get_device_status(self, device_id: str) -> str:
        return self.device_states.get(device_id, {}).get("status", "Offline")

    def update_last_activity(self, device_id: str, platform: str):
        state = self.device_states.setdefault(device_id, {})
        last = state.setdefault("last_activity", {})
        last[platform] = utils.timestamp_now()
        self._save_states()

    def get_last_activity(self, device_id: str, platform: str) -> Optional[float]:
        return self.device_states.get(device_id, {}).get("last_activity", {}).get(platform)

    def save_device_name(self, device_id, new_name):
        self.devices[device_id] = new_name
        found = False
        for dev in self.devices_info:
            if dev["id"] == device_id:
                dev["name"] = new_name
                found = True
                break
        if not found:
            self.devices_info.append({
                "id": device_id,
                "name": new_name,
                "accounts": self._get_account_count(device_id),
                "tiktok": self.get_account_counts(device_id)["TikTok"],
                "instagram": self.get_account_counts(device_id)["Instagram"],
            })
        self._save_devices_info()

    def add_device(self, device_id, nickname=None):
        if device_id not in self.devices:
            name = nickname or device_id
            self.devices[device_id] = name
            counts = self.get_account_counts(device_id)
            self.devices_info.append({
                "id": device_id,
                "name": name,
                "accounts": self._get_account_count(device_id),
                "tiktok": counts["TikTok"],
                "instagram": counts["Instagram"],
            })
            self._save_devices_info()
            self.set_device_status(device_id, "Idle")

    def remove_device(self, device_id):
        if device_id in self.devices:
            del self.devices[device_id]
            self.devices_info = [d for d in self.devices_info if d["id"] != device_id]
            self._save_devices_info()
        if device_id in self.device_states:
            del self.device_states[device_id]
            self._save_states()
    def update_nickname(self, device_id, nickname):
        self.save_device_name(device_id, nickname)

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
            self.update_device_accounts(device_id)

    def remove_account(self, device_id, platform, account_name):
        if device_id in self.accounts and platform in self.accounts[device_id]:
            accounts_list = self.accounts[device_id][platform]["accounts"]
            if account_name in accounts_list:
                accounts_list.remove(account_name)
                if self.accounts[device_id][platform]["active"] == account_name:
                    self.accounts[device_id][platform]["active"] = accounts_list[0] if accounts_list else None
                self.save_json(self.accounts_file, self.accounts)
                self.update_device_accounts(device_id)

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


def update_device(device_id, key, value):
    cm = ConfigManager()
    for device in cm.devices_info:
        if device.get('id') == device_id:
            device[key] = value
            cm._save_devices_info()
            break
