#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMULATOR PENGIRIM UDP JOYSTICK UNTUK PENGUJIAN GUI
Mengirimkan paket UDP ke 127.0.0.1:5005 untuk menguji respons GUI tanpa stik fisik.
"""

import socket
import json
import time
import math

TARGET_IP = "127.0.0.1"
TARGET_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("=" * 65)
print("     SIMULATOR PENGIRIM DATA JOYSTICK (UDP 5005)")
print(f" Mengirim ke {TARGET_IP}:{TARGET_PORT} (Tekan Ctrl+C untuk berhenti)")
print("=" * 65)

seq = 0
buttons_list = [2, 1, 3, 0, 4, 5, 8, 9, 12] # A, B, X, Y, LB, RB, select, start, home
step = 0

try:
    while True:
        now_ts = time.time()
        now_mono = time.monotonic()
        step += 1

        # 1. Simulasi Analog Stick (Pergerakan Berputar Halus)
        angle = step * 0.1
        axis_1_x = round(math.cos(angle) * 0.85, 3)
        axis_1_y = round(math.sin(angle) * 0.85, 3)

        # 2. Simulasi Trigger LT / RT (Analog)
        lt_val = round((math.sin(step * 0.05) + 1.0) / 2.0, 2)
        rt_val = round((math.cos(step * 0.05) + 1.0) / 2.0, 2)

        # 3. Simulasi Tekan Tombol Bergantian
        btn_idx = buttons_list[(step // 25) % len(buttons_list)]
        btn_state = 1 if (step % 25) < 15 else 0

        # Kirim paket Event Tombol
        pkt_btn = {
            "seq": seq,
            "timestamp": now_ts,
            "send_time": now_mono,
            "type": "button",
            "button": btn_idx,
            "value": btn_state
        }
        sock.sendto(json.dumps(pkt_btn).encode("utf-8"), (TARGET_IP, TARGET_PORT))
        seq += 1

        # Kirim paket Event Analog 1 X
        pkt_axis_x = {
            "seq": seq,
            "timestamp": now_ts,
            "send_time": now_mono,
            "type": "axis",
            "axis": 1,
            "value": axis_1_x
        }
        sock.sendto(json.dumps(pkt_axis_x).encode("utf-8"), (TARGET_IP, TARGET_PORT))
        seq += 1

        # Kirim paket Event Analog 1 Y
        pkt_axis_y = {
            "seq": seq,
            "timestamp": now_ts,
            "send_time": now_mono,
            "type": "axis",
            "axis": 0,
            "value": axis_1_y
        }
        sock.sendto(json.dumps(pkt_axis_y).encode("utf-8"), (TARGET_IP, TARGET_PORT))
        seq += 1

        # Kirim paket Event Trigger RT
        pkt_axis_rt = {
            "seq": seq,
            "timestamp": now_ts,
            "send_time": now_mono,
            "type": "axis",
            "axis": 5,
            "value": rt_val
        }
        sock.sendto(json.dumps(pkt_axis_rt).encode("utf-8"), (TARGET_IP, TARGET_PORT))
        seq += 1

        time.sleep(0.04) # ~25 Hz

except KeyboardInterrupt:
    print("\nSimulator dihentikan.")
finally:
    sock.close()
