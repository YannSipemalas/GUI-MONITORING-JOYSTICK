#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py – Jendela utama GUI Monitoring Joystick.
Menghubungkan UdpReceiverWorker, SerialTransceiverWorker,
dan panel-panel GUI.

Logika Watchdog yang DIPERBAIKI:
  • Watchdog hanya memonitor status link (UdpReceiverWorker menentukan CONNECTED/DISCONNECTED).
  • Tidak lagi memanggil reset_to_zero() hanya karena stik diam.
  • E-Stop memaksa serial kirim nol ke Teensy secara permanen sampai dilepas.
"""

import sys
import time
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QSplitter
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QFont

from udp_receiver       import UdpReceiverWorker
from serial_transceiver import SerialTransceiverWorker
from gui_panels         import (
    ConnectionPanel, JoystickPanel,
    TelemetryPanel, LogPanel, EStopPanel
)

# ─────────────────────────────────────────────────────────────
#  KONFIGURASI
# ─────────────────────────────────────────────────────────────
UDP_PORT     = 5005
SERIAL_PORT  = "/dev/ttyACM0"

APP_TITLE    = "GUI Monitoring Joystick – Robot AKI"
APP_VERSION  = "v2.1 (heartbeat)"


# ─────────────────────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE}  {APP_VERSION}")
        self.setMinimumSize(900, 640)
        self._last_link_status = ""

        # ── Panel-panel ──
        self._conn_panel  = ConnectionPanel()
        self._joy_panel   = JoystickPanel()
        self._tele_panel  = TelemetryPanel()
        self._log_panel   = LogPanel()
        self._estop_panel = EStopPanel()

        # ── Layout ──
        self._build_layout()

        # ── Worker Thread UDP ──
        self._udp = UdpReceiverWorker(port=UDP_PORT)
        self._udp.data_received.connect(self._on_udp_data)
        self._udp.status_changed.connect(self._on_udp_status)
        self._udp.stats_updated.connect(self._on_stats)
        self._udp.start()

        # ── Worker Thread Serial ──
        self._serial = SerialTransceiverWorker(port=SERIAL_PORT)
        self._serial.telemetry_received.connect(self._on_telemetry)
        self._serial.serial_status.connect(self._on_serial_status)
        self._serial.start()

        # ── E-Stop toggle ──
        self._estop_panel.btn.toggled.connect(self._on_estop_toggle)

        # ── Timer heartbeat status panel (setiap 500ms) ──
        self._hb_timer = QTimer(self)
        self._hb_timer.timeout.connect(self._update_heartbeat_display)
        self._hb_timer.start(500)

        self._log("Sistem dimulai.")
        self._log(f"Mendengarkan UDP port {UDP_PORT}.")
        self._log(f"Serial: {SERIAL_PORT}")

    # ──────────────────────────────────────────────────────────
    #  Layout
    # ──────────────────────────────────────────────────────────
    def _build_layout(self):
        central = QWidget()
        root    = QVBoxLayout()
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)

        # Header
        header = QHBoxLayout()
        title  = QLabel(APP_TITLE)
        title.setFont(QFont("Inter", 15, QFont.Bold))
        title.setStyleSheet("color:#e0e0e0;")
        self._clock_lbl = QLabel()
        self._clock_lbl.setStyleSheet("color:#546e7a; font-size:11px;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._clock_lbl)

        # Jam update setiap detik
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        root.addLayout(header)

        # E-Stop
        root.addWidget(self._estop_panel)

        # Baris atas: koneksi + joystick
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        top_row.addWidget(self._conn_panel, 1)
        top_row.addWidget(self._joy_panel,  2)
        root.addLayout(top_row)

        # Baris bawah: telemetri + log
        bot_row = QHBoxLayout()
        bot_row.setSpacing(8)
        bot_row.addWidget(self._tele_panel, 1)
        bot_row.addWidget(self._log_panel,  2)
        root.addLayout(bot_row)

        central.setLayout(root)
        self.setCentralWidget(central)

        # Stylesheet global (dark theme)
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #0d1117;
                color: #e0e0e0;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
        """)

    # ──────────────────────────────────────────────────────────
    #  Slot: Data UDP diterima
    # ──────────────────────────────────────────────────────────
    def _on_udp_data(self, data: dict):
        # Update panel joystick
        self._joy_panel.update_data(data)

        # Status Bluetooth dari Raspberry Pi
        bt_ok = data.get("joystick_connected", False)
        bt_str = "CONNECTED" if bt_ok else "DISCONNECTED"
        self._conn_panel.update_status("bluetooth", bt_str)

        # Teruskan perintah ke serial (jika tidak E-Stop)
        if not self._estop_panel.is_active():
            analog = data.get("analog", {})
            self._serial.set_command(analog)

    # ──────────────────────────────────────────────────────────
    #  Slot: Status UDP Link (CONNECTED / DISCONNECTED)
    # ──────────────────────────────────────────────────────────
    def _on_udp_status(self, status: str):
        if status == self._last_link_status:
            return
        self._last_link_status = status
        self._conn_panel.update_status("udp", status)

        ts = datetime.now().strftime("%H:%M:%S")
        if status == "DISCONNECTED":
            self._log(f"[{ts}] ⚠ UDP DISCONNECTED – tidak ada paket dari Raspberry Pi.")
            # Nolkan joystick display
            self._joy_panel.update_data({})
        else:
            self._log(f"[{ts}] ✓ UDP CONNECTED – paket diterima dari Raspberry Pi.")

    # ──────────────────────────────────────────────────────────
    #  Slot: Statistik UDP
    # ──────────────────────────────────────────────────────────
    def _on_stats(self, stats: dict):
        lat  = stats.get("latency_ms", 0)
        loss = stats.get("packet_loss", 0)
        self._log(f"[STATS] Latency: {lat:.1f} ms | Loss: {loss:.1f}%")

    # ──────────────────────────────────────────────────────────
    #  Slot: Telemetri dari Teensy
    # ──────────────────────────────────────────────────────────
    def _on_telemetry(self, tele: dict):
        self._tele_panel.update_telemetry(tele)

    # ──────────────────────────────────────────────────────────
    #  Slot: Status Serial
    # ──────────────────────────────────────────────────────────
    def _on_serial_status(self, status: str):
        self._conn_panel.update_status("serial", status)
        ts = datetime.now().strftime("%H:%M:%S")
        self._log(f"[{ts}] Serial: {status}")

    # ──────────────────────────────────────────────────────────
    #  Slot: E-Stop
    # ──────────────────────────────────────────────────────────
    def _on_estop_toggle(self, active: bool):
        self._serial.set_estop(active)
        ts  = datetime.now().strftime("%H:%M:%S")
        msg = (f"[{ts}] 🛑 E-STOP AKTIF – motor terkunci!"
               if active
               else f"[{ts}] ✓ E-STOP direset – sistem normal.")
        self._log(msg)

    # ──────────────────────────────────────────────────────────
    #  Heartbeat display: perbarui indikator setiap 500ms
    # ──────────────────────────────────────────────────────────
    def _update_heartbeat_display(self):
        elapsed = self._udp.last_rx_elapsed()
        if elapsed < 0.5:
            hb_str = f"OK ({elapsed*1000:.0f} ms)"
        elif elapsed < 1.5:
            hb_str = f"SLOW ({elapsed*1000:.0f} ms)"
        else:
            hb_str = "TIMEOUT"
        self._conn_panel.update_status("heartbeat", hb_str)

    # ──────────────────────────────────────────────────────────
    #  Jam
    # ──────────────────────────────────────────────────────────
    def _update_clock(self):
        self._clock_lbl.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    # ──────────────────────────────────────────────────────────
    #  Log helper
    # ──────────────────────────────────────────────────────────
    def _log(self, msg: str):
        self._log_panel.append(msg)

    # ──────────────────────────────────────────────────────────
    #  Cleanup
    # ──────────────────────────────────────────────────────────
    def closeEvent(self, event):
        self._udp.stop()
        self._serial.stop()
        event.accept()


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Inter", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
