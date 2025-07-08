import sys
import os
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTabWidget, QTextEdit, QListWidget, QLineEdit, QHBoxLayout,
    QMessageBox, QInputDialog
)
from PyQt5.QtCore import QTimer
from config_manager import ConfigManager
from appium_driver import AppiumDriver
from warmup_manager import WarmupManager
from post_manager import PostManager
from interaction_manager import InteractionManager
from session_summary import SessionSummary

class AutomationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Automation V7.1 - Ultimate Agency Edition")
        self.setGeometry(100, 100, 1400, 850)

        self.config = ConfigManager()
        self.driver = AppiumDriver()
        self.warmup_manager = WarmupManager(self.driver, self.config)
        self.post_manager = PostManager(self.driver, self.config)
        self.interaction_manager = InteractionManager(self.driver, self.config)
        self.session_summary = SessionSummary()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_tabs()
        self.show()

    def init_tabs(self):
        self.devices_tab()
        self.accounts_tab()
        self.warmup_tab()
        self.global_settings_tab()
        self.logs_tab()
        self.start_tab()

    def devices_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📱 Connected Devices:"))

        self.device_list = QListWidget()
        layout.addWidget(self.device_list)

        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        layout.addWidget(refresh_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Devices")
        self.refresh_devices()

    def refresh_devices(self):
        devices = self.driver.list_devices()
        self.device_list.clear()
        for device in devices:
            nickname = self.config.devices.get(device, device)
            self.device_list.addItem(f"{nickname} ({device})")

    def accounts_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🔑 Accounts per Device:"))

        self.accounts_container = QWidget()
        self.accounts_layout = QVBoxLayout()
        self.accounts_container.setLayout(self.accounts_layout)
        layout.addWidget(self.accounts_container)

        refresh_btn = QPushButton("Refresh Accounts")
        refresh_btn.clicked.connect(self.load_accounts)
        layout.addWidget(refresh_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Accounts")
        self.load_accounts()

    def load_accounts(self):
        for i in reversed(range(self.accounts_layout.count())):
            item = self.accounts_layout.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        for device_id, details in self.config.accounts.items():
            nickname = self.config.devices.get(device_id, device_id)
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{nickname} ({device_id})"))

            tiktok_active = details.get("TikTok", {}).get("active")
            tiktok_btn = QPushButton("Set Active TikTok")
            tiktok_btn.clicked.connect(lambda _, d=device_id: self.choose_active_account(d, "TikTok"))
            row.addWidget(QLabel(f"TikTok Active: {tiktok_active or 'None'}"))
            row.addWidget(tiktok_btn)

            instagram_active = details.get("Instagram", {}).get("active")
            insta_btn = QPushButton("Set Active Instagram")
            insta_btn.clicked.connect(lambda _, d=device_id: self.choose_active_account(d, "Instagram"))
            row.addWidget(QLabel(f"Instagram Active: {instagram_active or 'None'}"))
            row.addWidget(insta_btn)

            container = QWidget()
            container.setLayout(row)
            self.accounts_layout.addWidget(container)

    def choose_active_account(self, device_id, platform):
        accounts = self.config.accounts.get(device_id, {}).get(platform, {}).get("accounts", [])
        if not accounts:
            QMessageBox.warning(self, "No Accounts", f"No {platform} accounts for {device_id}")
            return
        account, ok = QInputDialog.getItem(self, f"Select Active {platform}", f"Choose account for {device_id}:", accounts, 0, False)
        if ok and account:
            self.config.set_active_account(device_id, platform, account)
            self.load_accounts()

    def warmup_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🔥 Warmup Phase Control:"))

        warmup_btn = QPushButton("Start Warmup For All")
        warmup_btn.clicked.connect(self.warmup_manager.start_all_warmup)
        layout.addWidget(warmup_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Warmup")

    def global_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("⚙️ Global Settings"))

        self.fast_bot_mode_btn = QPushButton("Toggle Fast Bot Mode (OFF)")
        self.fast_bot_mode_btn.setCheckable(True)
        self.fast_bot_mode_btn.clicked.connect(self.toggle_fast_bot_mode)
        layout.addWidget(self.fast_bot_mode_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Settings")

    def toggle_fast_bot_mode(self):
        state = self.fast_bot_mode_btn.isChecked()
        self.config.settings['fast_mode'] = state
        self.fast_bot_mode_btn.setText(f"Toggle Fast Bot Mode ({'ON' if state else 'OFF'})")
        self.config.save_json(self.config.settings_file, self.config.settings)

    def logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📜 Automation Logs:"))

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        refresh_btn = QPushButton("Refresh Logs")
        refresh_btn.clicked.connect(self.load_logs)
        layout.addWidget(refresh_btn)

        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.load_logs)
        self.log_timer.start(5000)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Logs")
        self.load_logs()

    def load_logs(self):
        log_file = os.path.join("Logs", "automation_log.txt")
        if not os.path.exists(log_file):
            self.log_view.setText("No logs found.")
            return

        lines = []
        with open(log_file, "r") as f:
            for line in f:
                color = "gray"
                if "SUCCESS" in line:
                    color = "green"
                elif "FAIL" in line:
                    color = "red"
                lines.append(f'<span style="color:{color}">{line.strip()}</span>')
        self.log_view.setHtml("<br>".join(lines))

    def start_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🚀 Start Automation"))

        start_btn = QPushButton("Start Automation")
        start_btn.clicked.connect(self.run_automation)
        layout.addWidget(start_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setCheckable(True)
        self.pause_btn.clicked.connect(self.toggle_pause)
        layout.addWidget(self.pause_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Start")

    def run_automation(self):
        self.post_manager.run()
        self.interaction_manager.run()

        def wait_for_completion():
            if self.post_manager.thread:
                self.post_manager.thread.join()
            if self.interaction_manager.thread:
                self.interaction_manager.thread.join()
            QTimer.singleShot(0, self.finish_session)

        threading.Thread(target=wait_for_completion, daemon=True).start()

    def finish_session(self):
        self.session_summary.show_summary()
        QMessageBox.information(self, "Session Complete", "Automation session completed successfully.")

    def toggle_pause(self):
        if self.pause_btn.isChecked():
            self.pause_btn.setText("Resume")
            self.post_manager.pause()
            self.interaction_manager.pause()
            self.warmup_manager.pause()
        else:
            self.pause_btn.setText("Pause")
            self.post_manager.resume()
            self.interaction_manager.resume()
            self.warmup_manager.resume()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AutomationGUI()
    sys.exit(app.exec_())
