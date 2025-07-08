import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTabWidget, QTextEdit, QListWidget, QLineEdit, QHBoxLayout, QMessageBox, QInputDialog
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
        layout = self.accounts_layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for device_id, details in self.config.accounts.items():
            nickname = self.config.devices.get(device_id, device_id)
            layout.addWidget(QLabel(f"{nickname} ({device_id}):"))

            tiktok_active = details.get("TikTok", {}).get("active", "None")
            tiktok_accounts = details.get("TikTok", {}).get("accounts", [])
            instagram_active = details.get("Instagram", {}).get("active", "None")
            instagram_accounts = details.get("Instagram", {}).get("accounts", [])

            info = "  TikTok: " + ", ".join([
                f"{acc}{' [✔️ Active]' if acc == tiktok_active else ''}" for acc in tiktok_accounts]) + "\n"
            info += "  Instagram: " + ", ".join([
                f"{acc}{' [✔️ Active]' if acc == instagram_active else ''}" for acc in instagram_accounts])
            info_label = QLabel(info)
            layout.addWidget(info_label)

            btn_layout = QHBoxLayout()
            tt_btn = QPushButton("Set Active TikTok")
            tt_btn.clicked.connect(lambda _, d=device_id: self.choose_active_account(d, "TikTok"))
            ig_btn = QPushButton("Set Active Instagram")
            ig_btn.clicked.connect(lambda _, d=device_id: self.choose_active_account(d, "Instagram"))
            btn_layout.addWidget(tt_btn)
            btn_layout.addWidget(ig_btn)
            layout.addLayout(btn_layout)

    def choose_active_account(self, device_id, platform):
        accounts = self.config.accounts.get(device_id, {}).get(platform, {}).get("accounts", [])
        if not accounts:
            QMessageBox.warning(self, "No Accounts", f"No {platform} accounts configured for {device_id}.")
            return
        account, ok = QInputDialog.getItem(self, f"Select Active {platform} Account", "Account:", accounts, 0, False)
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
        self.post_manager.run()
        self.interaction_manager.run()
        self.session_summary.show_summary()
        QMessageBox.information(self, "Session Complete", "Automation completed successfully.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AutomationGUI()
    sys.exit(app.exec_())
