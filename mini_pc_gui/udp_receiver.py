#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
udp_receiver.py  –  Worker thread penerima UDP dari Raspberry Pi.
Mendukung mode heartbeat 50Hz: koneksi tidak putus hanya karena stik diam.
"""

import json
import socket
import time
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

UDP_BUFFER = 4096
WATCHDOG_TIMEOUT = 1.5   # Detik tanpa paket → status DISCONNECTED


class UdpReceiverWorker(QThread):
    """
    QThread yang mendengarkan paket UDP dari Raspberry Pi.
    Sinyal:
      data_received(dict)  – paket valid diterima
      status_changed(str)  – 'CONNECTED' atau 'DISCONNECTED'
      stats_updated(dict)  – statistik latency / packet-loss
    """

    data_received  = pyqtSignal(dict)
    status_changed = pyqtSignal(str)
    stats_updated  = pyqtSignal(dict)

    def __init__(self, host: str = "0.0.0.0", port: int = 5005, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port

        self._running       = False
        self._mutex         = QMutex()
        self._current_data  : dict  = {}
        self._link_status   : str   = "DISCONNECTED"
        self._last_rx_time  : float = 0.0
        self._last_seq      : int   = -1
        self._total_pkts    : int   = 0
        self._lost_pkts     : int   = 0
        self._latencies     : list  = []

    # ------------------------------------------------------------------
    # Properti thread-safe
    # ------------------------------------------------------------------
    def get_current_data(self) -> dict:
        with QMutexLocker(self._mutex):
            return dict(self._current_data)

    def get_link_status(self) -> str:
        with QMutexLocker(self._mutex):
            return self._link_status

    def last_rx_elapsed(self) -> float:
        """Berapa detik sejak paket terakhir diterima."""
        with QMutexLocker(self._mutex):
            if self._last_rx_time == 0.0:
                return 9999.0
            return time.time() - self._last_rx_time

    def reset_to_zero(self):
        """
        Nolkan semua input state (dipanggil oleh watchdog di main.py).
        CATATAN: Sekarang watchdog hanya nolkan state, BUKAN ubah koneksi.
        Status koneksi ditentukan sendiri oleh worker ini berdasarkan timing.
        """
        with QMutexLocker(self._mutex):
            self._current_data = {}
        # Emit data kosong agar GUI update ke nol
        self.data_received.emit({
            "buttons": {},
            "analog": {"LT": 0.0, "RT": 0.0,
                       "axis_1_x": 0.0, "axis_1_y": 0.0,
                       "axis_2_x": 0.0, "axis_2_y": 0.0,
                       "dpad_x": 0.0,   "dpad_y": 0.0},
            "joystick_connected": False
        })

    # ------------------------------------------------------------------
    # Thread utama
    # ------------------------------------------------------------------
    def run(self):
        self._running = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.2)                # batas waktu non-blocking

        try:
            sock.bind((self.host, self.port))
            print(f"[UDP] Mendengarkan di {self.host}:{self.port}")
        except OSError as e:
            print(f"[UDP ERROR] Bind gagal: {e}")
            self._running = False
            return

        last_status_emitted = ""

        while self._running:
            # ---------- Terima Paket ----------
            try:
                raw, addr = sock.recvfrom(UDP_BUFFER)
                rx_time   = time.time()

                payload = json.loads(raw.decode("utf-8"))

                # Hitung latency (jika ada timestamp di paket)
                latency_ms = 0.0
                if "timestamp" in payload:
                    latency_ms = (rx_time - payload["timestamp"]) * 1000.0
                    self._latencies.append(latency_ms)
                    if len(self._latencies) > 100:
                        self._latencies.pop(0)

                # Hitung packet-loss dari sequence number
                seq = payload.get("seq", -1)
                if seq != -1:
                    if self._last_seq != -1 and seq > self._last_seq + 1:
                        self._lost_pkts += seq - self._last_seq - 1
                    self._last_seq  = seq
                    self._total_pkts += 1

                with QMutexLocker(self._mutex):
                    self._current_data = payload
                    self._last_rx_time = rx_time

                self.data_received.emit(dict(payload))

                # Emit statistik setiap 50 paket
                if self._total_pkts % 50 == 0:
                    avg_lat  = (sum(self._latencies) / len(self._latencies)
                                if self._latencies else 0.0)
                    loss_pct = (self._lost_pkts / max(1, self._total_pkts + self._lost_pkts)) * 100
                    self.stats_updated.emit({
                        "latency_ms"  : round(avg_lat, 1),
                        "packet_loss" : round(loss_pct, 2),
                        "total_pkts"  : self._total_pkts,
                    })

            except socket.timeout:
                pass   # normal, lanjut ke cek watchdog
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass   # paket rusak, abaikan
            except Exception as e:
                if self._running:
                    print(f"[UDP ERROR] {e}")

            # ---------- Watchdog status link ----------
            elapsed = self.last_rx_elapsed()
            new_status = "CONNECTED" if elapsed < WATCHDOG_TIMEOUT else "DISCONNECTED"

            with QMutexLocker(self._mutex):
                self._link_status = new_status

            if new_status != last_status_emitted:
                self.status_changed.emit(new_status)
                last_status_emitted = new_status

        sock.close()
        print("[UDP] Thread berhenti.")

    def stop(self):
        self._running = False
        self.wait(3000)
