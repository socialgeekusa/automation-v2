import os
import re
from PyQt5.QtWidgets import QMessageBox

class SessionSummary:
    def __init__(self):
        self.log_file = os.path.join("Logs", "automation_log.txt")

    def show_summary(self):
        """
        Reads the automation log and displays a summary popup.
        """
        if not os.path.exists(self.log_file):
            summary_text = "No logs found."
        else:
            actions = {}
            with open(self.log_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # Group by device/account prefix before the colon
                    key = re.split(r':', line, 1)[0]
                    actions[key] = actions.get(key, 0) + 1
            parts = [f"{key}: {count} actions" for key, count in actions.items()]
            summary_text = "\n".join(parts) if parts else "No actions logged."

        msg = QMessageBox()
        msg.setWindowTitle("Session Summary")
        msg.setText(summary_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
