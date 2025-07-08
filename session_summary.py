import os
import re
from PyQt5.QtWidgets import QMessageBox

class SessionSummary:
    def __init__(self):
        self.log_file = os.path.join("Logs", "automation_log.txt")
        self.post_log = os.path.join("Logs", "post_log.txt")

    def show_summary(self):
        """
        Reads the automation log and displays a summary popup.
        """
        actions = {}
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        _, rest = line.split(": ", 1)
                        device_id, _ = rest.split(": ", 1)
                    except ValueError:
                        continue
                    actions[device_id] = actions.get(device_id, 0) + 1

        if os.path.exists(self.post_log):
            with open(self.post_log, "r") as f:
                for line in f:
                    if "SUCCESS" in line:
                        try:
                            _, rest = line.split(": ", 1)
                            device_id, _ = rest.split(": ", 1)
                        except ValueError:
                            continue
                        actions[device_id] = actions.get(device_id, 0) + 1

        if actions:
            parts = [f"{key}: {count} actions" for key, count in actions.items()]
            summary_text = "\n".join(parts)
        else:
            summary_text = "No logs found."

        msg = QMessageBox()
        msg.setWindowTitle("Session Summary")
        msg.setText(summary_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
