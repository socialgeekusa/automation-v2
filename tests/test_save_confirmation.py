import os
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import main
from tests.test_manage_dialog import create_gui


def test_account_settings_save_shows_popup(tmp_path, monkeypatch):
    gui, app = create_gui(tmp_path)
    gui.config.add_device("dev1")
    gui.config.add_account("dev1", "TikTok", "user")

    dialog = main.AccountSettingsDialog(gui, "dev1", "TikTok", "user")

    called = {}

    def fake_info(*args, **kwargs):
        called["called"] = True

    monkeypatch.setattr(main.QMessageBox, "information", fake_info)

    dialog.settings_widget.likes_spin.setValue(5)
    dialog.save()

    assert called.get("called")
    assert gui.config.get_account_settings("user")["likes"] == 5

    dialog.close()
    gui.close()
    app.quit()


def test_settings_dialog_save_shows_popup(tmp_path, monkeypatch):
    gui, app = create_gui(tmp_path)

    dialog = main.SettingsDialog(gui)

    called = {}

    def fake_info(*args, **kwargs):
        called["called"] = True

    monkeypatch.setattr(main.QMessageBox, "information", fake_info)

    dialog.min_delay_spin.setValue(2)
    dialog.save_settings()

    assert called.get("called")
    assert gui.config.settings["min_delay"] == 2

    dialog.close()
    gui.close()
    app.quit()
