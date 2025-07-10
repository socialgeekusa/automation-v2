import os
import sys
import time
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from post_manager import PostManager
from interaction_manager import InteractionManager

class DummyDriver:
    def __init__(self, verify_result=False):
        self.verify_result = verify_result
        self.switch_called = False
        self.open_called = False
        self.open_draft_called = False
        self.start_called = False

    def start_session(self, device_id, platform):
        self.start_called = True

    def open_app(self, device_id, platform):
        self.open_called = True

    def open_first_draft(self, device_id, platform):
        self.open_draft_called = True

    def verify_current_account(self, device_id, platform, username):
        return self.verify_result

    def switch_account(self, device_id, platform, username):
        self.switch_called = True
        return True

class DummyConfig:
    def __init__(self):
        self.settings = {"min_delay": 0, "max_delay": 0}
        self.accounts = {
            "dev": {"TikTok": {"active": "user"}, "Instagram": {"active": None}}
        }

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


def test_post_loop_invokes_open_and_switch(tmp_path, monkeypatch):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    driver = DummyDriver()
    config = DummyConfig()
    pm = PostManager(driver, config)

    from post_manager import time as pm_time
    monkeypatch.setattr(pm_time, "sleep", lambda *a, **k: None)

    original_post = pm.post_draft

    def wrapped_post(*args, **kwargs):
        original_post(*args, **kwargs)
        pm.active = False

    monkeypatch.setattr(pm, "post_draft", wrapped_post)

    pm.active = True
    pm._post_loop()
    os.chdir(cwd)

    assert driver.open_called
    assert driver.switch_called


def test_post_draft_invokes_open_first_draft(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    driver = DummyDriver(verify_result=True)
    config = DummyConfig()
    pm = PostManager(driver, config)

    pm.post_draft("dev", "TikTok", "user")
    os.chdir(cwd)

    assert driver.open_draft_called


def test_interaction_loop_invokes_open_and_switch(tmp_path, monkeypatch):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    driver = DummyDriver()
    config = DummyConfig()
    im = InteractionManager(driver, config)

    from interaction_manager import time as im_time
    monkeypatch.setattr(im_time, "sleep", lambda *a, **k: None)

    original_perform = im.perform_interactions

    def wrapped_perform(*args, **kwargs):
        original_perform(*args, **kwargs)
        im.active = False

    monkeypatch.setattr(im, "perform_interactions", wrapped_perform)

    im.active = True
    im._interaction_loop()
    os.chdir(cwd)

    assert driver.open_called
    assert driver.switch_called
