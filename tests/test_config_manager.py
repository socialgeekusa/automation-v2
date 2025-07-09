import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config_manager


def create_cm(tmp_path):
    original_file = config_manager.__file__
    config_manager.__file__ = os.path.join(tmp_path, 'config_manager.py')
    cm = config_manager.ConfigManager()
    config_manager.__file__ = original_file
    return cm


def test_default_files_created(tmp_path):
    cm = create_cm(tmp_path)
    assert os.path.isdir(cm.config_folder)
    assert os.path.isfile(cm.devices_file)
    assert os.path.isfile(cm.accounts_file)
    assert os.path.isfile(cm.account_settings_file)
    assert os.path.isfile(cm.settings_file)
    assert cm.settings['fast_mode'] is False


def test_account_manipulation(tmp_path):
    cm = create_cm(tmp_path)
    cm.add_device('device1')
    cm.add_account('device1', 'TikTok', 'user1')
    assert cm.accounts['device1']['TikTok']['active'] == 'user1'
    cm.add_account('device1', 'TikTok', 'user2')
    cm.set_active_account('device1', 'TikTok', 'user2')
    assert cm.accounts['device1']['TikTok']['active'] == 'user2'
    cm.remove_account('device1', 'TikTok', 'user1')
    assert cm.accounts['device1']['TikTok']['accounts'] == ['user2']

    counts = cm.get_account_counts('device1')
    assert counts['TikTok'] == 1


def test_account_settings(tmp_path):
    cm = create_cm(tmp_path)
    cm.set_account_settings('user1', {'min_delay': 1})
    assert cm.get_account_settings('user1')['min_delay'] == 1


def test_save_device_name(tmp_path):
    cm = create_cm(tmp_path)
    cm.add_device('dev1')
    cm.save_device_name('dev1', 'Phone A')
    data = cm.load_json(cm.devices_file)
    assert any(d['id'] == 'dev1' and d['name'] == 'Phone A' for d in data['devices'])


def test_account_counts(tmp_path):
    cm = create_cm(tmp_path)
    cm.add_device('dev1')
    cm.add_account('dev1', 'TikTok', 'user1')
    cm.add_account('dev1', 'Instagram', 'insta1')
    counts = cm.get_account_counts('dev1')
    assert counts['TikTok'] == 1
    assert counts['Instagram'] == 1
    cm.remove_account('dev1', 'Instagram', 'insta1')
    counts = cm.get_account_counts('dev1')
    assert counts['Instagram'] == 0
    device = [d for d in cm.devices_info if d['id'] == 'dev1'][0]
    assert device['tiktok'] == 1 and device['instagram'] == 0
