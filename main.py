import sys
import os
import re
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QTextEdit,
    QHBoxLayout,
    QMessageBox,
    QInputDialog,
    QSpinBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QSplitter,
    QDialog,
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


class ManageDialog(QDialog):
    """Dialog for managing a single device's accounts."""

    def __init__(self, parent: "AutomationGUI", device_id: str):
        super().__init__(parent)
        self.gui = parent
        self.device_id = device_id
        self.setWindowTitle(f"Manage Device {device_id}")

        self.tables = {}
        layout = QVBoxLayout(self)

        for platform in ("TikTok", "Instagram"):
            layout.addWidget(QLabel(platform))
            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Account", "Active"])
            table.horizontalHeader().setStretchLastSection(True)
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.itemDoubleClicked.connect(
                lambda item, p=platform: self.gui.open_account_settings(
                    self.device_id, p, item.text()
                )
            )
            self.tables[platform] = table
            layout.addWidget(table)

            btn_row = QHBoxLayout()
            add_btn = QPushButton(f"Add {platform}")
            add_btn.clicked.connect(lambda _, p=platform: self.handle_add(p))
            remove_btn = QPushButton(f"Remove {platform}")
            remove_btn.clicked.connect(lambda _, p=platform: self.handle_remove(p))
            active_btn = QPushButton(f"Set Active {platform}")
            active_btn.clicked.connect(lambda _, p=platform: self.handle_active(p))
            for b in (add_btn, remove_btn, active_btn):
                btn_row.addWidget(b)
            layout.addLayout(btn_row)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.populate()

    def populate(self):
        """Load account info for both platforms into the tables."""
        data = self.gui.config.accounts.get(self.device_id, {})
        for platform, table in self.tables.items():
            info = data.get(platform, {})
            accounts = info.get("accounts", [])
            active = info.get("active")
            table.setRowCount(0)
            for row, acc in enumerate(accounts):
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(acc))
                table.setItem(row, 1, QTableWidgetItem("Yes" if acc == active else ""))

    def _refresh_all(self):
        """Refresh tables and parent views."""
        self.populate()
        self.gui.load_accounts()
        for table in (self.gui.android_table, self.gui.iphone_table):
            table.setRowCount(0)
        self.gui.load_devices_ui()

    def handle_add(self, platform: str):
        self.gui.add_account(self.device_id, platform)
        self._refresh_all()

    def handle_remove(self, platform: str):
        self.gui.remove_account(self.device_id, platform)
        self._refresh_all()

    def handle_active(self, platform: str):
        self.gui.choose_active_account(self.device_id, platform)
        self._refresh_all()

class AccountSettingsWidget(QWidget):
    """Widget for editing per-account settings."""

    def __init__(self, username: str, config: ConfigManager, warmup: WarmupManager):
        super().__init__()
        self.username = username
        self.config = config
        self.warmup = warmup

        layout = QVBoxLayout(self)

        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Min Delay (s):"))
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 120)
        min_layout.addWidget(self.min_spin)
        layout.addLayout(min_layout)

        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max Delay (s):"))
        self.max_spin = QSpinBox()
        self.max_spin.setRange(0, 120)
        max_layout.addWidget(self.max_spin)
        layout.addLayout(max_layout)

        current = self.config.get_account_settings(username)
        self.min_spin.setValue(current.get("min_delay", self.config.settings.get("min_delay", 5)))
        self.max_spin.setValue(current.get("max_delay", self.config.settings.get("max_delay", 15)))

        if self.warmup.is_warmup_active(username):
            self.min_spin.setEnabled(False)
            self.max_spin.setEnabled(False)

    def get_settings(self):
        return {"min_delay": self.min_spin.value(), "max_delay": self.max_spin.value()}

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
        self.logs_by_device = {}

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_tabs()
        self.show()

    def init_tabs(self):
        self.devices_tab()
        self.accounts_tab()
        self.global_settings_tab()
        self.logs_tab()
        self.start_tab()


    def devices_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(6)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #000; }")

        self.android_table = QTableWidget()
        self._setup_table(self.android_table)
        self.iphone_table = QTableWidget()
        self._setup_table(self.iphone_table)

        android_container = QWidget()
        android_layout = QVBoxLayout()
        android_layout.setContentsMargins(0, 0, 0, 0)
        android_layout.addWidget(QLabel("\ud83d\udcf1 Android Devices"))
        android_layout.addWidget(self.android_table)
        android_container.setLayout(android_layout)

        iphone_container = QWidget()
        iphone_layout = QVBoxLayout()
        iphone_layout.setContentsMargins(0, 0, 0, 0)
        iphone_layout.addWidget(QLabel("\ud83c\udf4f iPhone Devices"))
        iphone_layout.addWidget(self.iphone_table)
        iphone_container.setLayout(iphone_layout)

        self.splitter.addWidget(android_container)
        self.splitter.addWidget(iphone_container)

        layout.addWidget(self.splitter)

        self.last_scan_label = QLabel("Last Scanned: --:--:--")
        layout.addWidget(self.last_scan_label)

        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        layout.addWidget(self.refresh_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Devices")
        self.refresh_devices()

    def _setup_table(self, table: QTableWidget):
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["#", "Nickname", "TikTok", "IG", "Actions"])
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setStretchLastSection(True)
        hdr.setDefaultAlignment(Qt.AlignCenter)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.DoubleClicked)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setFixedHeight(400)
        table.itemChanged.connect(self.handle_name_change)

    def handle_name_change(self, item: QTableWidgetItem):
        if item.column() != 1:
            return
        device_id = item.data(Qt.UserRole)
        new_name = item.text().strip()[:30]
        if not new_name:
            QMessageBox.warning(self, "Invalid Name", "Device name cannot be blank")
            item.setText(self.config.devices.get(device_id, device_id))
            return
        self.config.save_device_name(device_id, new_name)

    def _add_device_row(self, table: QTableWidget, index: int, device_id: str, name: str, tiktok_count: int, ig_count: int):
        table.blockSignals(True)
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(str(index)))
        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.UserRole, device_id)
        table.setItem(row, 1, name_item)
        table.setItem(row, 2, QTableWidgetItem(str(tiktok_count)))
        table.setItem(row, 3, QTableWidgetItem(str(ig_count)))

        btn_start = QPushButton("Start")
        btn_manage = QPushButton("Manage")
        btn_delete = QPushButton("Delete")
        for btn in (btn_start, btn_manage, btn_delete):
            btn.setFixedHeight(24)

        btn_start.clicked.connect(lambda _, d=device_id, b=btn_start: self.start_device(d, b))
        btn_manage.clicked.connect(lambda _, d=device_id: self.manage_device(d))
        btn_delete.clicked.connect(lambda _, d=device_id: self.delete_device(d))

        action_widget = QWidget()
        hl = QHBoxLayout(action_widget)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(btn_start)
        hl.addWidget(btn_manage)
        hl.addWidget(btn_delete)
        table.setCellWidget(row, 4, action_widget)
        table.blockSignals(False)

    def start_device(self, device_id: str, button: QPushButton):
        self.config.set_device_status(device_id, "Active")
        self.config.update_last_activity(device_id, "TikTok")
        self.config.update_last_activity(device_id, "Instagram")
        button.setStyleSheet("background-color: blue; border-radius:4px")
        button.setText("Running")

    def manage_device(self, device_id: str):
        dialog = ManageDialog(self, device_id)
        dialog.exec_()
        self.load_accounts()
        self.refresh_devices()

    def delete_device(self, device_id: str):
        if (
            QMessageBox.question(
                self,
                "Delete Device",
                f"Are you sure you want to delete this device?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            self.config.remove_device(device_id)
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

        for table in [self.android_table, self.iphone_table]:
            table.setRowCount(0)

        self.load_devices_ui()

        if added or removed:
            QMessageBox.information(self, "Device Scan", f"{len(added)} devices added. {len(removed)} devices removed.")

    def load_devices_ui(self):
        iphone_idx = 1
        android_idx = 1
        for device in self.config.devices_info:
            os_type = utils.detect_device_os(device)
            name = device.get("name", device.get("id"))
            tiktok = device.get("tiktok", 0)
            ig = device.get("instagram", 0)
            if os_type == "iPhone":
                self._add_device_row(self.iphone_table, iphone_idx, device.get("id"), name, tiktok, ig)
                iphone_idx += 1
            else:
                self._add_device_row(self.android_table, android_idx, device.get("id"), name, tiktok, ig)
                android_idx += 1


    def accounts_tab(self):
        tab = QWidget()
        self.accounts_tab_widget = tab
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
            for table in (self.android_table, self.iphone_table):
                table.setRowCount(0)
            self.load_devices_ui()

    def add_account(self, device_id, platform):
        account, ok = QInputDialog.getText(
            self,
            f"Add {platform} Account",
            f"Enter {platform} username for {device_id}:"
        )
        if ok and account:
            self.config.add_account(device_id, platform, account)
            self.load_accounts()
            for table in (self.android_table, self.iphone_table):
                table.setRowCount(0)
            self.load_devices_ui()

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
            for table in (self.android_table, self.iphone_table):
                table.setRowCount(0)
            self.load_devices_ui()

    def open_account_settings(self, device_id, platform, username):
        """Open a dialog to edit per-account settings."""
        if hasattr(self, "accounts_tab_widget"):
            idx = self.tabs.indexOf(self.accounts_tab_widget)
            if idx != -1:
                self.tabs.setCurrentIndex(idx)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Settings for {username}")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Edit settings for {platform} account {username} on {device_id}"))

        settings_widget = AccountSettingsWidget(username, self.config, self.warmup_manager)
        layout.addWidget(settings_widget)

        if self.warmup_manager.is_warmup_active(username):
            layout.addWidget(QLabel("Warmup active: delay overrides are disabled."))

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        def save():
            self.config.set_account_settings(username, settings_widget.get_settings())
            dialog.accept()

        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()


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
