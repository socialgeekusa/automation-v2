import os
import sys
from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import config_manager
import main


def create_cm(tmp_path):
    original = config_manager.__file__
    config_manager.__file__ = os.path.join(tmp_path, 'config_manager.py')
    cm = config_manager.ConfigManager()
    config_manager.__file__ = original
    return cm


class DummyWarmup:
    def __init__(self, active):
        self.active = active

    def is_warmup_active(self, username):
        return self.active


def test_widget_disables_fields(tmp_path):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])
    cm = create_cm(tmp_path)
    widget = main.AccountSettingsWidget("user", cm, DummyWarmup(True))
    assert not widget.min_spin.isEnabled()
    assert not widget.likes_spin.isEnabled()
    widget.close()
    app.quit()


def test_widget_saves_settings(tmp_path):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])
    cm = create_cm(tmp_path)
    widget = main.AccountSettingsWidget("user", cm, DummyWarmup(False))
    widget.likes_spin.setValue(5)
    widget.draft_checkbox.setChecked(True)
    cm.set_account_settings("user", widget.get_settings())
    loaded = cm.get_account_settings("user")
    assert loaded["likes"] == 5
    assert loaded["draft_posts"] is True
    widget.close()
    app.quit()
