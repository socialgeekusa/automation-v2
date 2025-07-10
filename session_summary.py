from PyQt5.QtWidgets import QMessageBox
from log_summary import accumulate_logs, accumulate_logs_by_account, format_duration


class SessionSummary:
    def show_summary(self):
        """Read the log files and display a summary popup."""
        device_counts, start_dev, end_dev = accumulate_logs()
        user_counts, start_user, end_user = accumulate_logs_by_account()

        if not device_counts and not user_counts:
            summary_text = "No logs found."
        else:
            lines = []
            if device_counts:
                header = f"{'Device':<15}{'Likes':>6}{'Follows':>8}{'Comments':>10}{'Shares':>8}{'Posts':>7}"
                lines.extend([header, '-' * len(header)])
                for device, data in device_counts.items():
                    lines.append(
                        f"{device:<15}{data['likes']:>6}{data['follows']:>8}{data['comments']:>10}{data['shares']:>8}{data['posts']:>7}"
                    )
                lines.append("")

            if user_counts:
                header = f"{'Username':<15}{'Likes':>6}{'Follows':>8}{'Comments':>10}{'Shares':>8}{'Posts':>7}"
                lines.extend([header, '-' * len(header)])
                for user, data in user_counts.items():
                    lines.append(
                        f"{user:<15}{data['likes']:>6}{data['follows']:>8}{data['comments']:>10}{data['shares']:>8}{data['posts']:>7}"
                    )
                lines.append("")

            start_times = [t for t in (start_dev, start_user) if t]
            end_times = [t for t in (end_dev, end_user) if t]
            start = min(start_times) if start_times else None
            end = max(end_times) if end_times else None
            lines.append(f"Session duration: {format_duration(start, end)}")
            summary_text = "\n".join(lines)

        msg = QMessageBox()
        msg.setWindowTitle("Session Summary")
        msg.setText(summary_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
