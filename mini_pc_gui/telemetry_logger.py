# -*- coding: utf-8 -*-
"""
MODUL: telemetry_logger.py
Fungsi: Perekaman data telemetri time-series ke file CSV (Blackbox Data Logger).
"""

import os
import csv
from datetime import datetime


class TelemetryLogger:
    def __init__(self, log_dir="./logs"):
        self.log_dir = log_dir
        self.is_recording = False
        self.file_handle = None
        self.writer = None
        self.current_filename = ""

    def start_recording(self):
        """Memulai sesi perekaman data telemetri baru ke file CSV."""
        if self.is_recording:
            return self.current_filename

        try:
            os.makedirs(self.log_dir, exist_ok=True)
            ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_filename = os.path.join(self.log_dir, f"telemetry_{ts_str}.csv")
            
            self.file_handle = open(self.current_filename, "w", newline="", encoding="utf-8")
            self.writer = csv.writer(self.file_handle)
            
            # Header CSV Lengkap
            header = [
                "Timestamp", "Packets_Received", "Packets_Lost", "Latency_Avg_ms",
                "Btn_A", "Btn_B", "Btn_X", "Btn_Y", "Btn_LB", "Btn_RB",
                "Trigger_LT", "Trigger_RT", "Axis_1_X", "Axis_1_Y", "Axis_2_X", "Axis_2_Y"
            ]
            self.writer.writerow(header)
            self.is_recording = True
            return self.current_filename
        except Exception as e:
            print(f"[ERROR] Gagal memulai perekaman CSV: {e}")
            self.stop_recording()
            return None

    def log_snapshot(self, snap):
        """Mencatat 1 baris snapshot data telemetri ke file CSV."""
        if not self.is_recording or not self.writer:
            return

        try:
            btns = snap.get("buttons", {})
            axes = snap.get("axes", {})
            row = [
                datetime.now().strftime("%H:%M:%S.%f")[:-3],
                snap.get("received", 0),
                snap.get("lost", 0),
                f"{snap.get('latency_avg', 0.0):.2f}",
                btns.get("A", 0), btns.get("B", 0), btns.get("X", 0), btns.get("Y", 0),
                btns.get("LB", 0), btns.get("RB", 0),
                f"{snap.get('lt', 0.0):.2f}",
                f"{snap.get('rt', 0.0):.2f}",
                f"{axes.get(1, 0.0):.3f}",
                f"{axes.get(0, 0.0):.3f}",
                f"{axes.get(4, 0.0):.3f}",
                f"{axes.get(3, 0.0):.3f}"
            ]
            self.writer.writerow(row)
        except Exception as e:
            print(f"[WARN] Gagal menulis baris CSV: {e}")

    def stop_recording(self):
        """Menghentikan sesi perekaman dan menutup file."""
        self.is_recording = False
        if self.file_handle:
            try:
                self.file_handle.flush()
                self.file_handle.close()
            except Exception:
                pass
            self.file_handle = None
            self.writer = None
        saved_name = self.current_filename
        self.current_filename = ""
        return saved_name
