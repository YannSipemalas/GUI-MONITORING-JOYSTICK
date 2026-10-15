#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBOT SYSTEM MONITORING - MINI PC
File Utama (Entry Point) untuk Menjalankan Aplikasi GUI Monitoring.
"""

import sys
import os
import time
from datetime import datetime

# Tambahkan direktori saat ini ke sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import PyQt5 / PyQt6 Compatibility Shim
try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
    from PyQt5.QtCore import QTimer, Qt
except ImportError:
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
        from PyQt6.QtCore import QTimer, Qt
    except ImportError:
        print("[ERROR] PyQt5 atau PyQt6 tidak ditemukan! Silakan install: pip install PyQt5")
        sys.exit(1)

# Import Modul-Modul Sistem
from config_manager import load_config
from style_sheet import LIGHT_THEME_QSS
from udp_receiver import UdpReceiverWorker
from serial_transceiver import SerialTransceiverWorker
from telemetry_logger import TelemetryLogger
from gui_panels import HeaderWidget, JoystickInputPanel, TelemetryPanel, TeensyLogPanel, FooterWidget


class RobotMonitoringApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ROBOT SYSTEM MONITORING | MINI PC")
        self.resize(1366, 768)
        self.setMinimumSize(1100, 680)

        # Muat Konfigurasi
        self.cfg = load_config()

        # Inisialisasi State & Logger
        self.last_rx_time  = None
        self.estop_active  = False
        # State koneksi saat ini — hanya update UI jika benar-benar berubah
        self._conn_state   = {"wifi": None, "bluetooth": None, "serial": None}

        # --- WiFi state machine ---
        self.wifi_state  = "wait"   # "conn" | "weak" | "wait"
        self.rx_streak   = 0        # paket beruntun (gap < STREAK_GAP)
        self.last_change = 0.0      # monotonic time saat badge terakhir berubah
        log_dir = self.cfg["logging"].get("log_directory", "./logs")
        self.logger = TelemetryLogger(log_dir=log_dir)

        # Setup Tampilan & Gaya Visual
        self.setup_ui()
        self.setStyleSheet(LIGHT_THEME_QSS)

        # Inisialisasi Worker Threads
        self.udp_worker = UdpReceiverWorker(self.cfg)
        self.serial_worker = SerialTransceiverWorker(self.cfg, self.udp_worker)

        # Hubungkan Sinyal-Sinyal Antarmuka
        self.connect_signals()

        # Jalankan Background Threads
        self.udp_worker.start()
        self.serial_worker.start()

        # Inisialisasi Timer Watchdog (100ms) & Clock (1000ms)
        self.timer_watchdog = QTimer(self)
        self.timer_watchdog.timeout.connect(self.watchdog_check)
        self.timer_watchdog.start(100)

        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_clock)
        self.timer_clock.start(1000)

        self.append_system_log("INFO", "Sistem Monitoring diinisialisasi pada Mini PC.")
        self.append_system_log("INFO", f"Mendengarkan data UDP di Port {self.cfg['network']['udp_listen_port']}...")

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        root_layout = QVBoxLayout(main_widget)
        root_layout.setContentsMargins(16, 12, 16, 12)
        root_layout.setSpacing(10)

        # 1. Header Bar
        self.header = HeaderWidget(self)
        self.header.btn_estop.clicked.connect(self.toggle_estop)
        root_layout.addWidget(self.header)

        # 2. Body - Layout 3 Kolom
        body_layout = QHBoxLayout()
        body_layout.setSpacing(12)

        # Kolom 1: Joystick Input Panel
        self.panel_joystick = JoystickInputPanel(self)
        body_layout.addWidget(self.panel_joystick)

        # Kolom 2: Telemetry & Statistics Panel
        self.panel_telemetry = TelemetryPanel(self)
        body_layout.addWidget(self.panel_telemetry, stretch=3)

        # Kolom 3: Teensy Serial & Log Panel
        self.panel_teensy = TeensyLogPanel(self.cfg["serial"], self)
        self.panel_teensy.btn_clear.clicked.connect(self.clear_system_log)
        self.panel_teensy.btn_rec.clicked.connect(self.toggle_recording)
        body_layout.addWidget(self.panel_teensy, stretch=3)

        root_layout.addLayout(body_layout, stretch=1)

        # 3. Footer Bar
        self.footer = FooterWidget(cfg=self.cfg, parent=self)
        root_layout.addLayout(self.footer)

    def connect_signals(self):
        # Sinyal dari UDP Receiver
        self.udp_worker.telemetry_updated.connect(self.on_telemetry_updated)
        self.udp_worker.log_event.connect(self.append_system_log)
        self.udp_worker.connection_changed.connect(self.update_connection_status)

        # Sinyal dari Serial Transceiver
        self.serial_worker.serial_status_changed.connect(self.on_serial_status_changed)
        self.serial_worker.serial_tx_event.connect(self.panel_teensy.append_serial_text)
        self.serial_worker.serial_rx_event.connect(self.panel_teensy.append_serial_text)
        self.serial_worker.log_event.connect(self.append_system_log)

    def on_telemetry_updated(self, snap):
        now = time.monotonic()
        # Hitung streak: paket beruntun dengan jeda antar paket < STREAK_GAP
        # Keputusan status WiFi TIDAK dibuat di sini — serahkan ke watchdog_check
        if self.last_rx_time is not None and (now - self.last_rx_time) < self.STREAK_GAP:
            self.rx_streak += 1
        else:
            self.rx_streak = 1           # mulai ulang hitungan
        self.last_rx_time = now

        # Bluetooth: ikuti flag joystick_connected dari Raspberry Pi
        # (hanya update saat WiFi aktif; jika WiFi hilang, watchdog yang atur BT)
        bt = getattr(self.udp_worker, "_bt_state", None)
        if bt is False:
            self.set_badge("bluetooth", "disc")
        else:
            self.set_badge("bluetooth", "conn")

        # Perbarui Kolom 1 (Tombol & Analog)
        self.panel_joystick.update_inputs(snap["buttons"], snap["lt"], snap["rt"], axes=snap.get("axes", {}))
        # Perbarui Kolom 2 (Statistik)
        self.panel_telemetry.update_telemetry(snap)
        # Rekam ke CSV jika aktif
        if self.logger.is_recording:
            self.logger.log_snapshot(snap)

    # Konstanta state machine WiFi
    STREAK_GAP     = 0.05   # detik — jeda maks antar paket agar dihitung beruntun
    RECONNECT_PKTS = 25     # streak minimum sebelum naik ke CONNECTED (~0.5 s @ 50 Hz)
    UP_DWELL       = 1.0    # detik — jeda minimum antara dua perubahan naik
    WEAK_AFTER_SEC = 1.0    # detik tanpa paket → SINYAL LEMAH
    WAIT_AFTER_SEC = 3.0    # detik tanpa paket → MENUNGGU PAKET
    _RANK = {"wait": 0, "weak": 1, "conn": 2}

    # Tabel teks & nama style per state
    _BADGE = {
        "conn": ("● CONNECTED",      "NodeBadgeConn"),
        "weak": ("● SINYAL LEMAH",   "NodeBadgeWeak"),
        "wait": ("○ MENUNGGU PAKET", "NodeBadgeWaiting"),   # WiFi: abu/oranye
        "disc": ("● DISCONNECTED",   "NodeBadgeDisconn"),   # BT & Serial: merah
    }

    def set_badge(self, device, state):
        # Hanya update UI jika status benar-benar berubah
        if self._conn_state.get(device) == state:
            return
        prev = self._conn_state.get(device)
        self._conn_state[device] = state
        node = {"wifi": self.panel_telemetry.node_wifi,
                "bluetooth": self.panel_telemetry.node_bt}.get(device)
        if node is None:
            return
        text, obj = self._BADGE[state]
        b = node.badge_label
        b.setText(text)
        b.setObjectName(obj)
        b.setStyle(b.style())
        name = "WiFi/UDP" if device == "wifi" else "Bluetooth joystick"
        if state == "disc" and prev is not None:
            self.append_system_log("ERROR", f"{name} DISCONNECTED")
        elif state == "conn" and prev in ("disc", "weak"):
            self.append_system_log("INFO", f"{name} CONNECTED kembali")

    def update_connection_status(self, device, is_connected):
        # Sinyal dari UdpReceiverWorker — hanya untuk Bluetooth
        # Status WiFi dikelola penuh oleh watchdog_check (state machine)
        if device == "bluetooth":
            self.set_badge("bluetooth", "conn" if is_connected else "disc")

    def on_serial_status_changed(self, is_connected, port):
        # Hanya update UI jika status benar-benar berubah
        if self._conn_state.get("serial") == is_connected:
            return
        self._conn_state["serial"] = is_connected
        self.panel_teensy.update_serial_status(is_connected)
        b = self.panel_telemetry.node_serial.badge_label
        b.setText("● CONNECTED" if is_connected else "● DISCONNECTED")
        b.setObjectName("NodeBadgeConn" if is_connected else "NodeBadgeDisconn")
        b.setStyle(b.style())

    def append_system_log(self, level, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        color = "#1E293B"
        if level == "WARN": color = "#D97706"
        elif level == "ERROR": color = "#DC2626"
        elif level == "INFO": color = "#2563EB"

        html_entry = f'<span style="color:#64748B;">[{ts}]</span> <span style="font-weight:bold; color:{color};">[{level}]</span> {msg}'
        self.panel_teensy.append_log_html(html_entry)

    def clear_system_log(self):
        self.panel_teensy.txt_log.clear()

    def toggle_recording(self):
        if not self.logger.is_recording:
            saved_file = self.logger.start_recording()
            if saved_file:
                self.panel_teensy.btn_rec.setText("■ Stop CSV")
                self.panel_teensy.btn_rec.setStyleSheet("background-color: #FEE2E2; color: #DC2626; border-color: #FCA5A5;")
                self.append_system_log("INFO", f"Mulai merekam telemetri ke {saved_file}")
        else:
            saved_file = self.logger.stop_recording()
            self.panel_teensy.btn_rec.setText("● Rec CSV")
            self.panel_teensy.btn_rec.setStyleSheet("")
            self.append_system_log("INFO", f"Perekaman telemetri dihentikan. Disimpan: {saved_file}")

    def toggle_estop(self):
        self.estop_active = not self.estop_active
        if self.estop_active:
            self.header.btn_estop.setText("⚠️ ESTOP ACTIVE (RESET)")
            self.header.btn_estop.setStyleSheet("background-color: #991B1B; color: #FEF08A; font-weight: 800;")
            self.append_system_log("ERROR", "🚨 EMERGENCY STOP DIAKTIFKAN! Seluruh perintah motor dihentikan.")
            self.udp_worker.reset_to_zero()
        else:
            self.header.btn_estop.setText("🚨 E-STOP (SPACE)")
            self.header.btn_estop.setStyleSheet("")
            self.append_system_log("INFO", "Emergency Stop di-reset ke status normal.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.toggle_estop()
        else:
            super().keyPressEvent(event)

    def watchdog_check(self):
        """Dijalankan tiap 100 ms oleh QTimer.
        Satu-satunya tempat yang boleh mengubah status badge WiFi.
        Menggunakan hysteresis dua arah:
          - Turun: mengikuti gap nyata (langsung, tanpa tunda).
          - Naik : hanya setelah rx_streak >= RECONNECT_PKTS dan UP_DWELL terpenuhi.
        """
        if self.last_rx_time is None:
            return   # belum ada paket masuk sama sekali

        now    = time.monotonic()
        gap    = now - self.last_rx_time
        cur    = self.wifi_state
        stable = (self.rx_streak >= self.RECONNECT_PKTS) and (gap < 0.5)

        # Tentukan state baru berdasarkan gap dan streak
        if gap > self.WAIT_AFTER_SEC:
            new = "wait"
        elif cur == "wait":
            new = "conn" if stable else "wait"   # dari wait hanya bisa naik ke conn
        elif gap > self.WEAK_AFTER_SEC:
            new = "weak"
        elif cur == "weak":
            new = "conn" if stable else "weak"
        else:
            new = "conn"

        if new == cur:
            return

        # Perubahan NAIK: tahan minimal UP_DWELL detik sejak perubahan terakhir
        if self._RANK[new] > self._RANK[cur] and (now - self.last_change) < self.UP_DWELL:
            return

        # Terapkan perubahan
        prev = cur
        self.wifi_state  = new
        self.last_change = now
        self.set_badge("wifi", new)
        self._log_wifi_change(prev, new, gap)

        # Saat WiFi hilang: BT juga tidak bisa diketahui + failsafe motor
        if new == "wait":
            self.set_badge("bluetooth", "wait")
            self.udp_worker.reset_to_zero()
            self.panel_telemetry.lbl_pkt_rate.setText("0.00 packet/s")

    def _log_wifi_change(self, prev, new, gap):
        label = {"conn": "CONNECTED", "weak": "SINYAL LEMAH", "wait": "MENUNGGU PAKET"}
        msg   = f"WiFi: {label[prev]} → {label[new]}  (gap {gap:.1f} s)"
        if self._RANK[new] < self._RANK[prev]:   # turun
            level = "ERROR" if new == "wait" else "WARN"
        else:                                     # naik
            level = "INFO"
        self.append_system_log(level, msg)

    def update_clock(self):
        self.header.lbl_clock.setText(datetime.now().strftime("🕒 %Y-%m-%d %H:%M:%S"))

    def closeEvent(self, event):
        if self.logger.is_recording:
            self.logger.stop_recording()
        self.udp_worker.stop()
        self.serial_worker.stop()
        self.udp_worker.wait(500)
        self.serial_worker.wait(500)
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = RobotMonitoringApp()
    window.show()
    sys.exit(app.exec_() if hasattr(app, 'exec_') else app.exec())


if __name__ == "__main__":
    main()
