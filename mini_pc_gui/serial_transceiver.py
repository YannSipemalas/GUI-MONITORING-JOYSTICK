#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
serial_transceiver.py – Worker thread serial ke Teensy @ 115200 / 50Hz.
Jika E-Stop aktif, selalu kirim nol (mesin tidak bergerak).
"""

import json
import time
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

SERIAL_BAUD = 115200
SEND_HZ     = 50          # Hz kirim ke Teensy
CMD_TIMEOUT = 2.0         # detik sebelum auto-stop jika tidak ada cmd baru


class SerialTransceiverWorker(QThread):
    """
    Mengirim perintah motor ke Teensy @50Hz via serial,
    dan membaca telemetri balik dari Teensy.
    """

    telemetry_received = pyqtSignal(dict)    # telemetri dari Teensy
    serial_status      = pyqtSignal(str)     # 'OPEN' / 'CLOSED' / 'ERROR'

    def __init__(self, port: str = "/dev/ttyACM0", parent=None):
        super().__init__(parent)
        self.port     = port
        self._running = False
        self._mutex   = QMutex()
        self._estop   = False
        self._cmd     : dict = {}
        self._last_cmd_time : float = 0.0

    # ------------------------------------------------------------------
    # API dari luar (thread-safe)
    # ------------------------------------------------------------------
    def set_command(self, cmd: dict):
        """Perbarui perintah motor dari GUI / UDP."""
        with QMutexLocker(self._mutex):
            self._cmd           = dict(cmd)
            self._last_cmd_time = time.time()

    def set_estop(self, active: bool):
        """Aktifkan / matikan E-Stop (semua nol saat aktif)."""
        with QMutexLocker(self._mutex):
            self._estop = active

    def is_estop(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._estop

    # ------------------------------------------------------------------
    # Thread utama
    # ------------------------------------------------------------------
    def run(self):
        self._running = True
        period        = 1.0 / SEND_HZ
        next_time     = time.monotonic()

        ser = None
        while self._running:
            # ---------- Buka serial jika belum terbuka ----------
            if ser is None or not ser.is_open:
                try:
                    ser = serial.Serial(self.port, SERIAL_BAUD, timeout=0.05)
                    self.serial_status.emit("OPEN")
                    print(f"[SERIAL] Terhubung ke {self.port} @ {SERIAL_BAUD}")
                except serial.SerialException as e:
                    self.serial_status.emit("CLOSED")
                    print(f"[SERIAL] Gagal buka port: {e}")
                    time.sleep(2.0)
                    continue

            # ---------- Siapkan perintah ----------
            with QMutexLocker(self._mutex):
                estop   = self._estop
                cmd     = dict(self._cmd)
                cmd_age = time.time() - self._last_cmd_time if self._last_cmd_time > 0 else 9999

            # Jika E-Stop atau sudah terlalu lama tidak ada perintah baru → kirim nol
            if estop or cmd_age > CMD_TIMEOUT:
                cmd = {
                    "LT": 0.0, "RT": 0.0,
                    "axis_1_x": 0.0, "axis_1_y": 0.0,
                    "axis_2_x": 0.0, "axis_2_y": 0.0
                }

            # ---------- Kirim ke Teensy ----------
            try:
                line = json.dumps(cmd, separators=(",", ":")) + "\n"
                ser.write(line.encode("utf-8"))
            except serial.SerialException as e:
                print(f"[SERIAL] Error kirim: {e}")
                ser = None
                self.serial_status.emit("ERROR")

            # ---------- Baca balasan dari Teensy (non-blocking) ----------
            try:
                if ser and ser.in_waiting:
                    raw = ser.readline().decode("utf-8", errors="replace").strip()
                    if raw:
                        tele = json.loads(raw)
                        self.telemetry_received.emit(tele)
            except Exception:
                pass

            # ---------- Jaga timing 50Hz ----------
            next_time += period
            sleep_t    = next_time - time.monotonic()
            if sleep_t > 0:
                time.sleep(sleep_t)
            else:
                next_time = time.monotonic()

        if ser and ser.is_open:
            ser.close()
        self.serial_status.emit("CLOSED")
        print("[SERIAL] Thread berhenti.")

    def stop(self):
        self._running = False
        self.wait(3000)
