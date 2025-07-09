import os
import sys
import json

from PyQt5.QtWidgets import QApplication, QInputDialog

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import config_manager
import main


def create_gui(tmp_path):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])
    original_file = config_manager.__file__
    config_manager.__file__ = os.path.join(tmp_path, "config_manager.py")
    gui = main.AutomationGUI()
    config_manager.__file__ = original_file
    return gui, app


def test_dialog_persists_accounts(tmp_path, monkeypatch):
    gui, app = create_gui(tmp_path)
    gui.config.add_device("dev1")
    dialog = main.ManageDialog(gui, "dev1")

    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("t_user", True))
    dialog.handle_add("TikTok")
    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("i_user", True))
    dialog.handle_add("Instagram")

    accounts = json.load(open(gui.config.accounts_file))
    assert accounts["dev1"]["TikTok"]["accounts"] == ["t_user"]
    assert accounts["dev1"]["Instagram"]["accounts"] == ["i_user"]

    gui.close()
    app.quit()

