import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import warmup_manager
import config_manager

class DummyDriver:
    def verify_current_account(self, device_id, platform, account):
        return True

def create_cm(tmp_path):
    original_file = config_manager.__file__
    config_manager.__file__ = os.path.join(tmp_path, 'config_manager.py')
    cm = config_manager.ConfigManager()
    config_manager.__file__ = original_file
    return cm


def test_is_warmup_active(tmp_path):
    cm = create_cm(tmp_path)
    driver = DummyDriver()
    wm = warmup_manager.WarmupManager(driver, cm)
    wm.progress_file = os.path.join(tmp_path, 'progress.json')
    wm.progress = {}
    wm._save_progress()

    assert wm.is_warmup_active('user1')
    wm.progress['user1'] = wm.total_days
    wm._save_progress()
    assert not wm.is_warmup_active('user1')
