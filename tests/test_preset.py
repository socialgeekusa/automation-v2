import os
import sys

from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config_manager import SLOW_HUMAN_PRESET
import main
from tests.test_manage_dialog import create_gui


def test_apply_preset_updates_settings_and_ui(tmp_path):
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

    gui.close()
    app.quit()

