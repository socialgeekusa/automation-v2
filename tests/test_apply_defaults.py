import os
import sys
import random
from PyQt5.QtWidgets import QApplication, QMessageBox

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import main
from tests.test_manage_dialog import create_gui


def test_apply_defaults_skips_warmup(tmp_path, monkeypatch):
    gui, app = create_gui(tmp_path)
    gui.config.add_device('dev1')
    gui.config.add_account('dev1', 'TikTok', 'warm')
    gui.config.add_account('dev1', 'Instagram', 'cold')

    gui.config.settings['min_delay'] = 7
    gui.config.settings['max_delay'] = 8
    gui.config.settings['interaction_ranges'] = {'likes': [1, 1], 'daily_posts': [2, 2]}
    gui.config.settings['draft_posts'] = True
    gui.config.save_json(gui.config.settings_file, gui.config.settings)

    monkeypatch.setattr(gui.warmup_manager, 'is_warmup_active', lambda u: u == 'warm')
    monkeypatch.setattr(random, 'randint', lambda a, b: a)
    monkeypatch.setattr(QMessageBox, 'information', lambda *a, **k: None)

    gui.apply_defaults_to_all()

    warm_settings = gui.config.get_account_settings('warm')
    cold_settings = gui.config.get_account_settings('cold')

    assert warm_settings == {}
    assert cold_settings['min_delay'] == 7
    assert cold_settings['max_delay'] == 8
    assert cold_settings['likes'] == 1
    assert cold_settings['daily_posts'] == 2
    assert cold_settings['draft_posts'] is True

    gui.close()
    app.quit()
