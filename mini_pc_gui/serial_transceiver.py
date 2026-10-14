# -*- coding: utf-8 -*-
"""
MODUL: serial_transceiver.py
Fungsi: Worker thread pengirim perintah ke Teensy (50 Hz) & penerima umpan balik (RX).
"""

import time
import json

try:
    from PyQt5.QtCore import QThread, pyqtSignal
except ImportError:
    from PyQt6.QtCore import QThread, pyqtSignal

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

from config_manager import DPAD_X_AXIS, DPAD_Y_AXIS


class SerialTransceiverWorker(QThread):
    serial_status_changed = pyqtSignal(bool, str) # (is_connected, port_name)
    serial_tx_event = pyqtSignal(str)             # Pesan terkirim
    serial_rx_event = pyqtSignal(str)             # Pesan diterima
    log_event = pyqtSignal(str, str)              # (level, message)

    def __init__(self, cfg, udp_worker):
        super().__init__()
        self.cfg = cfg
        self.udp_worker = udp_worker
        self.running = True
        self.is_connected = False
        self.ser = None

    def build_teensy_packet(self):
        """Menyusun struktur paket JSON yang dikirimkan ke Teensy (Sesuai joy.py)."""
        with self.udp_worker.lock:
            btns = dict(self.udp_worker.buttons)
            axes = dict(self.udp_worker.analog_axes)
            lt = self.udp_worker.lt_val
            rt = self.udp_worker.rt_val

        dx = axes.get(DPAD_X_AXIS, 0.0)
        dy = axes.get(DPAD_Y_AXIS, 0.0)

        pkt = {
            "Analog 1 X": round(axes.get(1, 0.0), 3),
            "Analog 1 Y": round(axes.get(0, 0.0), 3),
            "Analog 2 X": round(axes.get(4, 0.0), 3),
            "Analog 2 Y": round(axes.get(3, 0.0), 3),
            "buttons": {
                "Y": btns.get("Y", 0),
                "B": btns.get("B", 0),
                "A": btns.get("A", 0),
                "X": btns.get("X", 0),
                "LB": btns.get("LB", 0),
                "RB": btns.get("RB", 0),
                "LT": int(lt > 0.5),
                "RT": int(rt > 0.5),
                "select": btns.get("select", 0),
                "start": btns.get("start", 0),
                "home": btns.get("home", 0),
                "up": int(dy < -0.5),
                "down": int(dy > 0.5),
                "left": int(dx < -0.5),
                "right": int(dx > 0.5)
            }
        }
        return pkt

    def run(self):
        port = self.cfg["serial"].get("port", "/dev/ttyACM0")
        baud = self.cfg["serial"].get("baudrate", 115200)
        send_hz = self.cfg["serial"].get("send_hz", 50)
        period = 1.0 / send_hz if send_hz > 0 else 0.02
        reconn_interval = self.cfg["serial"].get("reconnect_interval_sec", 1.0)

        next_time = time.monotonic()

        while self.running:
            # 1. Buka Port Serial jika belum tersambung
            if self.ser is None:
                if SERIAL_AVAILABLE:
                    try:
                        self.ser = serial.Serial(port, baud, timeout=0)
                        self.is_connected = True
                        self.serial_status_changed.emit(True, port)
                        self.log_event.emit("INFO", f"Berhasil tersambung ke Teensy di {port} ({baud} Baud)")
                    except Exception:
                        self.ser = None
                        self.is_connected = False
                        self.serial_status_changed.emit(False, port)
                        time.sleep(reconn_interval)
                        continue
                else:
                    self.is_connected = False
                    self.serial_status_changed.emit(False, port)
                    time.sleep(reconn_interval)
                    continue

            # 2. Pengiriman Data Rutin (50 Hz)
            try:
                packet = self.build_teensy_packet()
                line = json.dumps(packet, separators=(",", ":")) + "\n"
                self.ser.write(line.encode("utf-8"))
                self.serial_tx_event.emit(f"[TX] {line.strip()[:65]}...")

                # 3. Baca Respons Balik dari Teensy (RX)
                if self.ser.in_waiting > 0:
                    rx_raw = self.ser.readline().decode("utf-8", errors="ignore").strip()
                    if rx_raw:
                        self.serial_rx_event.emit(f"[RX] {rx_raw}")
            except Exception as e:
                self.log_event.emit("WARN", f"Koneksi Serial Teensy terputus: {e}")
                self.is_connected = False
                self.serial_status_changed.emit(False, port)
                if self.ser:
                    try: self.ser.close()
                    except Exception: pass
                self.ser = None
                time.sleep(reconn_interval)
                continue

            # 4. Timer Delay Stabil 50 Hz
            next_time += period
            sleep_time = next_time - time.monotonic()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_time = time.monotonic()

        if self.ser:
            try: self.ser.close()
            except Exception: pass

    def stop(self):
        self.running = False
