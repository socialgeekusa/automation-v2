import os
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import main
from config_manager import SLOW_HUMAN_PRESET
from tests.test_manage_dialog import create_gui


def test_apply_defaults_skips_warmup(tmp_path, monkeypatch):
    gui, app = create_gui(tmp_path)
    gui.config.add_device('dev1')
    gui.config.add_account('dev1', 'TikTok', 'warm')
    gui.config.add_account('dev1', 'Instagram', 'cold')

    gui.config.settings['min_delay'] = 7
    gui.config.settings['max_delay'] = 8
    gui.config.settings['interaction_ranges'] = {'likes': [1, 5], 'daily_posts': [2, 7]}
    gui.config.settings['draft_posts'] = True
    gui.config.save_json(gui.config.settings_file, gui.config.settings)

    monkeypatch.setattr(gui.warmup_manager, 'is_warmup_active', lambda u: u == 'warm')
    monkeypatch.setattr(QMessageBox, 'information', lambda *a, **k: None)

    gui.apply_defaults_to_all()

    warm_settings = gui.config.get_account_settings('warm')
    cold_settings = gui.config.get_account_settings('cold')

    assert warm_settings == {}
    assert cold_settings['min_delay'] == 7
    assert cold_settings['max_delay'] == 8
    assert cold_settings['likes'] == 5
    assert cold_settings['daily_posts'] == 7
    assert cold_settings['draft_posts'] is True

    gui.close()
    app.quit()


def test_apply_defaults_platform_filter(tmp_path, monkeypatch):
    gui, app = create_gui(tmp_path)
    gui.config.add_device('dev1')
    gui.config.add_account('dev1', 'TikTok', 't_user')
    gui.config.add_account('dev1', 'Instagram', 'i_user')

    gui.config.settings['min_delay'] = 3
    gui.config.settings['max_delay'] = 4
    gui.config.settings['interaction_ranges'] = {'likes': [2, 9]}
    gui.config.settings['draft_posts'] = False
    gui.config.save_json(gui.config.settings_file, gui.config.settings)

    monkeypatch.setattr(gui.warmup_manager, 'is_warmup_active', lambda u: False)
    monkeypatch.setattr(QMessageBox, 'information', lambda *a, **k: None)

    gui.apply_defaults_to_all({'TikTok'})

    t_settings = gui.config.get_account_settings('t_user')
    i_settings = gui.config.get_account_settings('i_user')

    assert t_settings['likes'] == 9
    assert i_settings == {}

    gui.close()
    app.quit()


def test_apply_defaults_no_popup(tmp_path, monkeypatch):
    gui, app = create_gui(tmp_path)
    gui.config.add_device('dev1')
    gui.config.add_account('dev1', 'TikTok', 'user')

    monkeypatch.setattr(gui.warmup_manager, 'is_warmup_active', lambda u: False)
    called = []

    def fake_info(*a, **k):
        called.append(True)

    monkeypatch.setattr(QMessageBox, 'information', fake_info)

    gui.apply_defaults_to_all(show_popup=False)

    assert not called

    gui.close()
    app.quit()


def test_run_automation_applies_defaults(tmp_path, monkeypatch):
    gui, app = create_gui(tmp_path)

    recorded = {}

    def fake_apply_defaults(platforms=None, show_popup=True):
        recorded['show_popup'] = show_popup

    monkeypatch.setattr(gui, 'apply_defaults_to_all', fake_apply_defaults)
    monkeypatch.setattr(gui.session_summary, 'show_summary', lambda: None)
    monkeypatch.setattr(gui.interaction_manager, 'run', lambda: None)
    monkeypatch.setattr(gui.post_manager, 'run', lambda: None)
    monkeypatch.setattr(QMessageBox, 'information', lambda *a, **k: None)

    gui.run_automation()

    assert recorded.get('show_popup') is False

    gui.close()
    app.quit()


def test_apply_preset_populates_gui_and_settings(tmp_path):
    gui, app = create_gui(tmp_path)

    gui.apply_preset(SLOW_HUMAN_PRESET)

    assert gui.config.settings["min_delay"] == SLOW_HUMAN_PRESET["min_delay"]
    assert gui.min_delay_spin.value() == SLOW_HUMAN_PRESET["min_delay"]
    likes_range = SLOW_HUMAN_PRESET["interaction_ranges"]["likes"]
    stored_range = gui.config.settings["interaction_ranges"]["likes"]
    spin_min = gui.range_spins["likes"][0].value()
    spin_max = gui.range_spins["likes"][1].value()

    assert stored_range == likes_range
    assert spin_min == likes_range[0]
    assert spin_max == likes_range[1]
    assert gui.draft_checkbox.isChecked() == SLOW_HUMAN_PRESET["draft_posts"]

    gui.close()
    app.quit()
