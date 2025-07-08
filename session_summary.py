from PyQt5.QtWidgets import QMessageBox
from log_summary import accumulate_logs, format_duration


class SessionSummary:
    def show_summary(self):
        """Read the log files and display a summary popup."""
        counts, start, end = accumulate_logs()
        if not counts:
            summary_text = "No logs found."
        else:
            header = f"{'Device':<15}{'Likes':>6}{'Follows':>8}{'Comments':>10}{'Shares':>8}{'Posts':>7}"
            lines = [header, '-' * len(header)]
            for device, data in counts.items():
                lines.append(
                    f"{device:<15}{data['likes']:>6}{data['follows']:>8}{data['comments']:>10}{data['shares']:>8}{data['posts']:>7}"
                )
            lines.append("")
            lines.append(f"Session duration: {format_duration(start, end)}")
            summary_text = "\n".join(lines)

        msg = QMessageBox()
        msg.setWindowTitle("Session Summary")
        msg.setText(summary_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
