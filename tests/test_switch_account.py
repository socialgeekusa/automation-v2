import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from post_manager import PostManager
from interaction_manager import InteractionManager

class DummyDriver:
    def __init__(self, verify_result=False):
        self.verify_result = verify_result
        self.switch_called = False
    def verify_current_account(self, device_id, platform, username):
        return self.verify_result
    def switch_account(self, device_id, platform, username):
        self.switch_called = True
        return True

class DummyConfig:
    def __init__(self):
        self.settings = {"min_delay": 0, "max_delay": 0}
    def get_account_settings(self, username):
        return {}
    def update_last_activity(self, device_id, platform):
        pass


def test_post_manager_attempts_switch(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    driver = DummyDriver()
    config = DummyConfig()
    pm = PostManager(driver, config)
    pm.post_draft("dev", "TikTok", "user")
    os.chdir(cwd)
    assert driver.switch_called


def test_interaction_manager_attempts_switch(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    driver = DummyDriver()
    config = DummyConfig()
    im = InteractionManager(driver, config)
    im.perform_interactions("dev", "TikTok", "user")
    os.chdir(cwd)
    assert driver.switch_called
