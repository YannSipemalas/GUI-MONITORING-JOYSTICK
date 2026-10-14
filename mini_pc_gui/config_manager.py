# -*- coding: utf-8 -*-
"""
MODUL: config_manager.py
Fungsi: Mengelola pembacaan config.json dan pemetaan tombol/sumbu joystick.
"""

import os
import json

# Pemetaan ID Tombol Standar (Sesuai Pygame di Raspberry Pi & joy.py)
BUTTON_NAMES = {
    0: "Y",
    1: "B",
    2: "A",
    3: "X",
    4: "LB",
    5: "RB",
    6: "LT",
    7: "RT",
    8: "select",
    9: "start",
    12: "home"
}

# Pemetaan Sumbu Analog (Axis)
AXIS_MAP = {
    "Analog 1 X": 1,
    "Analog 1 Y": 0,
    "Analog 2 Y": 3,
    "Analog 2 X": 4,
}

DPAD_X_AXIS = 6
DPAD_Y_AXIS = 7

DEFAULT_CONFIG = {
    "network": {
        "udp_listen_ip": "0.0.0.0",
        "udp_listen_port": 5005,
        "buffer_size": 4096,
        "watchdog_timeout_sec": 1.0
    },
    "serial": {
        "port": "/dev/ttyACM0",
        "baudrate": 115200,
        "send_hz": 50,
        "reconnect_interval_sec": 1.0
    },
    "joystick": {
        "deadzone_threshold": 0.05,
        "invert_y_axis": False
    },
    "thresholds": {
        "packet_loss_warn_percent": 5.0,
        "latency_warn_ms": 150.0
    },
    "logging": {
        "auto_save_log": True,
        "log_directory": "./logs"
    }
}


def get_config_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "config.json")


def load_config():
    """Membaca konfigurasi dari config.json."""
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Gagal membaca config.json: {e}. Menggunakan konfigurasi default.")
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    """Menyimpan konfigurasi ke config.json."""
    path = get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan config.json: {e}")
        return False
