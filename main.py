import sys
import os
import re
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTabWidget, QTextEdit, QLineEdit, QHBoxLayout,
    QMessageBox, QInputDialog, QSpinBox, QComboBox,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import QTimer, Qt
import time
from config_manager import ConfigManager
import utils
from appium_driver import AppiumDriver
from warmup_manager import WarmupManager
from post_manager import PostManager
from interaction_manager import InteractionManager
from session_summary import SessionSummary

class AutomationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XO v1.1 - Ultimate Agency Edition")
        self.setGeometry(100, 100, 1400, 850)

        self.config = ConfigManager()
        self.driver = AppiumDriver()
        self.warmup_manager = WarmupManager(self.driver, self.config)
        self.post_manager = PostManager(self.driver, self.config)
        self.interaction_manager = InteractionManager(self.driver, self.config)
        self.session_summary = SessionSummary()
        self.warmup_labels = {}
        self.warmup_timer = QTimer()
        self.logs_by_device = {}

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

    class DeviceRow(QWidget):
        def __init__(self, parent, device_id, name, counts, os_type):
            super().__init__()
            self.gui = parent
            self.device_id = device_id
            self.os_type = os_type

            row = QHBoxLayout()
            row.setContentsMargins(10, 10, 10, 10)
            row.setSpacing(10)

            row.addWidget(QLabel(device_id))

            name_layout = QHBoxLayout()
            self.name_edit = QLineEdit(name)
            self.name_edit.setMaxLength(30)
            self.name_edit.editingFinished.connect(self.save_name)
            name_layout.addWidget(self.name_edit)
            self.status_badge = QLabel()
            self.status_badge.setFixedSize(10, 10)
            name_layout.addWidget(self.status_badge)
            name_container = QWidget()
            name_container.setLayout(name_layout)
            row.addWidget(name_container)

            self.accounts_label = QLabel(self._format_counts(counts))
            row.addWidget(self.accounts_label)

            self.activity_label = QLabel(self._activity_text())
            row.addWidget(self.activity_label)

            self.start_btn = QPushButton("Start")
            self.start_btn.setStyleSheet("background-color: green; border-radius:4px; padding:4px")
            self.start_btn.clicked.connect(self.start_device)
            self._apply_shadow(self.start_btn)
            row.addWidget(self.start_btn)

            manage_btn = QPushButton("Manage")
            manage_btn.setStyleSheet("background-color: #FFA500; border-radius:4px; padding:4px")
            manage_btn.clicked.connect(self.manage_device)
            self._apply_shadow(manage_btn)
            row.addWidget(manage_btn)

            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet("background-color: red; border-radius:4px; padding:4px")
            del_btn.clicked.connect(self.delete_device)
            self._apply_shadow(del_btn)
            row.addWidget(del_btn)

            self.setLayout(row)
            self.setStyleSheet("border:1px solid #ccc; border-radius:8px; padding:8px; margin-bottom:6px")
            self.update_status_badge()
            if self.gui.config.get_device_status(self.device_id) == "Active":
                self.start_btn.setStyleSheet("background-color: blue; border-radius:4px")
                self.start_btn.setText("Running")

        def _format_counts(self, counts):
            return f"TikTok: {counts.get('TikTok',0)} | Instagram: {counts.get('Instagram',0)}"

        def _activity_text(self):
            tt = self.gui.config.get_last_activity(self.device_id, "TikTok")
            ig = self.gui.config.get_last_activity(self.device_id, "Instagram")
            return f"TT: {utils.format_last_activity(tt)} | IG: {utils.format_last_activity(ig)}"

        def update_activity_label(self):
            self.activity_label.setText(self._activity_text())

        def update_status_badge(self):
            status = self.gui.config.get_device_status(self.device_id)
            color = {
                "Active": "green",
                "Idle": "yellow",
                "Offline": "red",
            }.get(status, "gray")
            self.status_badge.setStyleSheet(f"border-radius:5px;background-color:{color}")

        def _apply_shadow(self, button):
            effect = QGraphicsDropShadowEffect(self)
            effect.setBlurRadius(8)
            effect.setOffset(0, 2)
            button.setGraphicsEffect(effect)

        def save_name(self):
            new_name = self.name_edit.text().strip()[:30]
            if not new_name:
                QMessageBox.warning(self, "Invalid Name", "Device name cannot be blank")
                self.name_edit.setText(self.gui.config.devices.get(self.device_id, self.device_id))
                return
            self.gui.config.save_device_name(self.device_id, new_name)

        def start_device(self):
            self.gui.config.set_device_status(self.device_id, "Active")
            self.gui.config.update_last_activity(self.device_id, "TikTok")
            self.gui.config.update_last_activity(self.device_id, "Instagram")
            self.start_btn.setStyleSheet("background-color: blue; border-radius:4px")
            self.start_btn.setText("Running")
            self.update_status_badge()
            self.update_activity_label()

        def add_account(self):
            QMessageBox.information(self, "Add Account", "Feature coming soon")

        def manage_device(self):
            QMessageBox.information(self, "Manage Device", "Feature coming soon")

        def delete_device(self):
            if QMessageBox.question(self, "Delete Device", f"Are you sure you want to delete this device?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.gui.config.remove_device(self.device_id)
                self.gui.refresh_devices()

    def devices_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(QLabel("📱 Connected Devices:"))

        columns = QHBoxLayout()
        columns.setSpacing(20)
        columns.setContentsMargins(10, 0, 10, 0)

        self.android_container = QWidget()
        self.android_layout = QVBoxLayout()
        self.android_container.setLayout(self.android_layout)
        android_col = QVBoxLayout()
        android_col.addWidget(QLabel("Androids"))
        android_col.addWidget(self.android_container)
        columns.addLayout(android_col, 1)

        self.ios_container = QWidget()
        self.ios_layout = QVBoxLayout()
        self.ios_container.setLayout(self.ios_layout)
        ios_col = QVBoxLayout()
        ios_col.addWidget(QLabel("iPhones"))
        ios_col.addWidget(self.ios_container)
        columns.addLayout(ios_col, 1)

        layout.addLayout(columns)

        self.last_scan_label = QLabel("Last Scanned: --:--:--")
        layout.addWidget(self.last_scan_label)

        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        layout.addWidget(self.refresh_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Devices")
        self.refresh_devices()

    def refresh_devices(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Scanning...")
        self.last_scan_label.setText("Scanning...")
        QApplication.processEvents()

        prev_devices = set(self.config.devices.keys())
        scanned = set(self.driver.list_devices())
        self.last_scan_label.setText(f"Last Scanned: {time.strftime('%H:%M:%S')}")
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Refresh Devices")

        added = scanned - prev_devices
        removed = prev_devices - scanned

        for dev in added:
            self.config.add_device(dev)
            self.config.update_device_accounts(dev)
            self.config.set_device_status(dev, "Idle")
        for dev in removed:
            self.config.set_device_status(dev, "Offline")
        for dev in scanned:
            self.config.update_device_accounts(dev)

        for layout in [self.android_layout, self.ios_layout]:
            while layout.count():
                item = layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()

        all_devices = list(self.config.devices.keys())
        ios_rows = []
        android_rows = []
        for dev in all_devices:
            name = self.config.devices.get(dev, dev)
            counts = self.config.get_account_counts(dev)
            os_type = utils.detect_os(dev)
            row = self.DeviceRow(self, dev, name, counts, os_type)
            if os_type == "iOS":
                ios_rows.append((name.lower(), row))
            else:
                android_rows.append((name.lower(), row))

        for _, row in sorted(ios_rows, key=lambda x: x[0]):
            self.ios_layout.addWidget(row)
        for _, row in sorted(android_rows, key=lambda x: x[0]):
            self.android_layout.addWidget(row)

        if added or removed:
            QMessageBox.information(self, "Device Scan", f"{len(added)} devices added. {len(removed)} devices removed.")


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

        device_ids = set(self.driver.list_devices()) | set(self.config.accounts.keys())
        for device_id in sorted(device_ids):
            details = self.config.accounts.get(device_id, {})
            nickname = self.config.devices.get(device_id, device_id)
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{nickname} ({device_id})"))

            tiktok_active = details.get("TikTok", {}).get("active")
            row.addWidget(QLabel(f"TikTok Active: {tiktok_active or 'None'}"))
            tiktok_btn = QPushButton("Set Active TikTok")
            tiktok_btn.clicked.connect(lambda _, d=device_id: self.choose_active_account(d, "TikTok"))
            row.addWidget(tiktok_btn)
            add_tiktok = QPushButton("Add TikTok Account")
            add_tiktok.clicked.connect(lambda _, d=device_id: self.add_account(d, "TikTok"))
            row.addWidget(add_tiktok)
            remove_tiktok = QPushButton("Remove TikTok Account")
            remove_tiktok.clicked.connect(lambda _, d=device_id: self.remove_account(d, "TikTok"))
            row.addWidget(remove_tiktok)

            instagram_active = details.get("Instagram", {}).get("active")
            row.addWidget(QLabel(f"Instagram Active: {instagram_active or 'None'}"))
            insta_btn = QPushButton("Set Active Instagram")
            insta_btn.clicked.connect(lambda _, d=device_id: self.choose_active_account(d, "Instagram"))
            row.addWidget(insta_btn)
            add_instagram = QPushButton("Add Instagram Account")
            add_instagram.clicked.connect(lambda _, d=device_id: self.add_account(d, "Instagram"))
            row.addWidget(add_instagram)
            remove_instagram = QPushButton("Remove Instagram Account")
            remove_instagram.clicked.connect(lambda _, d=device_id: self.remove_account(d, "Instagram"))
            row.addWidget(remove_instagram)

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

    def add_account(self, device_id, platform):
        account, ok = QInputDialog.getText(
            self,
            f"Add {platform} Account",
            f"Enter {platform} username for {device_id}:"
        )
        if ok and account:
            self.config.add_account(device_id, platform, account)
            self.load_accounts()

    def remove_account(self, device_id, platform):
        accounts = self.config.accounts.get(device_id, {}).get(platform, {}).get("accounts", [])
        if not accounts:
            QMessageBox.warning(self, "No Accounts", f"No {platform} accounts for {device_id}")
            return
        account, ok = QInputDialog.getItem(
            self,
            f"Remove {platform} Account",
            f"Select {platform} account to remove from {device_id}:",
            accounts,
            0,
            False
        )
        if ok and account:
            self.config.remove_account(device_id, platform, account)
            self.load_accounts()

    def warmup_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🔥 Warmup Phase Control:"))

        self.warmup_container = QWidget()
        self.warmup_layout = QVBoxLayout()
        self.warmup_container.setLayout(self.warmup_layout)
        layout.addWidget(self.warmup_container)

        warmup_btn = QPushButton("Start Warmup For All")
        warmup_btn.clicked.connect(self.warmup_manager.start_all_warmup)
        layout.addWidget(warmup_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Warmup")
        self.load_warmup_progress()
        self.warmup_timer.timeout.connect(self.load_warmup_progress)
        self.warmup_timer.start(5000)

    def load_warmup_progress(self):
        for i in reversed(range(self.warmup_layout.count())):
            item = self.warmup_layout.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        progress = self.warmup_manager.get_progress()
        for device_id in self.config.accounts:
            nickname = self.config.devices.get(device_id, device_id)
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{nickname} ({device_id})"))
            day = progress.get(device_id, 0)
            label = QLabel(f"Day {day} of {self.warmup_manager.total_days}")
            row.addWidget(label)
            self.warmup_labels[device_id] = label
            container = QWidget()
            container.setLayout(row)
            self.warmup_layout.addWidget(container)

    def global_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("⚙️ Global Settings"))

        self.fast_bot_mode_btn = QPushButton("Toggle Fast Bot Mode (OFF)")
        self.fast_bot_mode_btn.setCheckable(True)
        self.fast_bot_mode_btn.clicked.connect(self.toggle_fast_bot_mode)
        layout.addWidget(self.fast_bot_mode_btn)

        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Min Delay (s):"))
        self.min_delay_spin = QSpinBox()
        self.min_delay_spin.setRange(0, 120)
        self.min_delay_spin.setValue(self.config.settings.get("min_delay", 5))
        self.min_delay_spin.valueChanged.connect(self.update_delay_settings)
        delay_layout.addWidget(self.min_delay_spin)

        delay_layout.addWidget(QLabel("Max Delay (s):"))
        self.max_delay_spin = QSpinBox()
        self.max_delay_spin.setRange(0, 120)
        self.max_delay_spin.setValue(self.config.settings.get("max_delay", 15))
        self.max_delay_spin.valueChanged.connect(self.update_delay_settings)
        delay_layout.addWidget(self.max_delay_spin)

        layout.addLayout(delay_layout)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Settings")

    def toggle_fast_bot_mode(self):
        state = self.fast_bot_mode_btn.isChecked()
        self.config.settings['fast_mode'] = state
        self.fast_bot_mode_btn.setText(f"Toggle Fast Bot Mode ({'ON' if state else 'OFF'})")
        self.config.save_json(self.config.settings_file, self.config.settings)

    def update_delay_settings(self):
        min_val = self.min_delay_spin.value()
        max_val = self.max_delay_spin.value()
        if min_val > max_val:
            if self.sender() is self.min_delay_spin:
                self.max_delay_spin.setValue(min_val)
                max_val = min_val
            else:
                self.min_delay_spin.setValue(max_val)
                min_val = max_val
        self.config.settings['min_delay'] = min_val
        self.config.settings['max_delay'] = max_val
        self.config.save_json(self.config.settings_file, self.config.settings)

    def logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📜 Automation Logs:"))

        self.device_selector = QComboBox()
        self.device_selector.currentIndexChanged.connect(self.update_log_view)
        layout.addWidget(self.device_selector)

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
            self.logs_by_device = {}
            self.device_selector.clear()
            self.device_selector.addItem("All Devices", None)
            self.log_view.setText("No logs found.")
            return

        device_logs = {}
        prefix_re = re.compile(r"^\[(\S+)\]")
        suffix_re = re.compile(r"on\s+([\w-]+)\b")
        with open(log_file, "r") as f:
            for raw in f:
                line = raw.strip()
                match = prefix_re.match(line)
                if match:
                    device = match.group(1)
                else:
                    match = suffix_re.search(line)
                    device = match.group(1) if match else "Unknown"
                device_logs.setdefault(device, []).append(line)

        self.logs_by_device = device_logs

        current = self.device_selector.currentData()
        self.device_selector.blockSignals(True)
        self.device_selector.clear()
        self.device_selector.addItem("All Devices", None)
        for dev in sorted(device_logs.keys()):
            self.device_selector.addItem(dev, dev)
        self.device_selector.blockSignals(False)
        if current in device_logs or current is None:
            idx = self.device_selector.findData(current)
            if idx != -1:
                self.device_selector.setCurrentIndex(idx)
        self.update_log_view()

    def update_log_view(self):
        device = self.device_selector.currentData()
        lines = []
        if device is None:
            for dev_lines in self.logs_by_device.values():
                lines.extend(dev_lines)
        else:
            lines = self.logs_by_device.get(device, [])

        formatted = []
        for line in lines:
            color = "gray"
            if "SUCCESS" in line:
                color = "green"
            elif "FAIL" in line or "ERROR" in line:
                color = "red"
            formatted.append(f'<span style="color:{color}">{line}</span>')

        if formatted:
            self.log_view.setHtml("<br>".join(formatted))
        else:
            self.log_view.setText("No logs for this device.")

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

        # wait for both managers to finish before showing results
        if self.post_manager.thread:
            self.post_manager.thread.join()
        if self.interaction_manager.thread:
            self.interaction_manager.thread.join()

        self.session_summary.show_summary()
        QMessageBox.information(self, "Session Complete", "Automation tasks have completed.")

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
