import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTabWidget, QTextEdit, QListWidget, QLineEdit, QHBoxLayout, QMessageBox, QInputDialog
)
from PyQt5.QtCore import QTimer, QThread, QObject, pyqtSignal
from config_manager import ConfigManager
from appium_driver import AppiumDriver
from warmup_manager import WarmupManager
from post_manager import PostManager
from interaction_manager import InteractionManager
from session_summary import SessionSummary


class AutomationWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, post_manager, interaction_manager):
        super().__init__()
        self.post_manager = post_manager
        self.interaction_manager = interaction_manager

    def run(self):
        self.post_manager.run()
        self.interaction_manager.run()
        self.post_manager.join()
        self.interaction_manager.join()
        self.finished.emit()

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

        self.accounts_text = QTextEdit()
        self.accounts_text.setReadOnly(True)
        layout.addWidget(self.accounts_text)

        refresh_btn = QPushButton("Refresh Accounts")
        refresh_btn.clicked.connect(self.load_accounts)
        layout.addWidget(refresh_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Accounts")
        self.load_accounts()

    def load_accounts(self):
        accounts_display = ""
        for device_id, details in self.config.accounts.items():
            nickname = self.config.devices.get(device_id, device_id)
            accounts_display += f"{nickname} ({device_id}):\n"
            tiktok_active = details.get("TikTok", {}).get("active", "None")
            tiktok_accounts = details.get("TikTok", {}).get("accounts", [])
            instagram_active = details.get("Instagram", {}).get("active", "None")
            instagram_accounts = details.get("Instagram", {}).get("accounts", [])

            accounts_display += "  TikTok: " + ", ".join([
                f"{acc}{' [✔️ Active]' if acc == tiktok_active else ''}" for acc in tiktok_accounts]) + "\n"
            accounts_display += "  Instagram: " + ", ".join([
                f"{acc}{' [✔️ Active]' if acc == instagram_active else ''}" for acc in instagram_accounts]) + "\n\n"
        self.accounts_text.setText(accounts_display)

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

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Logs")
        self.load_logs()

    def load_logs(self):
        log_file = os.path.join("Logs", "automation_log.txt")
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                self.log_view.setText(f.read())
        else:
            self.log_view.setText("No logs found.")

    def start_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🚀 Start Automation"))

        start_btn = QPushButton("Start Automation")
        start_btn.clicked.connect(self.run_automation)
        layout.addWidget(start_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Start")

    def run_automation(self):
        self.thread = QThread()
        self.worker = AutomationWorker(self.post_manager, self.interaction_manager)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.session_complete)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def session_complete(self):
        self.session_summary.show_summary()
        QMessageBox.information(self, "Session Complete", "Automation completed successfully.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AutomationGUI()
    sys.exit(app.exec_())
