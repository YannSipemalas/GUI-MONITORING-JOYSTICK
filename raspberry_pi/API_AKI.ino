#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RASPBERRY PI - PENGIRIM DATA JOYSTICK (API_AKI)
Mengirim paket UDP penuh setiap 20ms (50Hz) walaupun stik diam.
Ini adalah HEARTBEAT mode — bukan event-based lagi.
"""

import pygame
import socket
import json
import time
import threading

# =========================
# KONFIGURASI
# =========================
PC_IP   = "192.168.0.200"  # Ganti dengan IP Mini PC Anda
PC_PORT = 5005
SEND_HZ = 50               # Frekuensi kirim paket (heartbeat)

# =========================
# UDP SOCKET
# =========================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# =========================
# JOYSTICK (PYGAME)
# =========================
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("[ERROR] Joystick tidak ditemukan!")
    raise SystemExit

joystick = pygame.joystick.Joystick(0)
joystick.init()

print("=" * 55)
print("  RASPBERRY PI – JOYSTICK UDP SENDER (HEARTBEAT 50Hz)")
print("=" * 55)
print(f"Joystick : {joystick.get_name()}")
print(f"Axis     : {joystick.get_numaxes()}")
print(f"Buttons  : {joystick.get_numbuttons()}")
print(f"Target   : {PC_IP}:{PC_PORT}")
print(f"Rate     : {SEND_HZ} Hz")
print()

# =========================
# PEMETAAN TOMBOL
# =========================
# Sesuaikan dengan jenis stik Anda:
# PS4: A=0,B=1,X=2,Y=3 / Xbox: A=0,B=1,X=2,Y=3 / Generic: bisa berbeda
BUTTON_MAP = {
    "Y"     : 0,
    "B"     : 1,
    "A"     : 2,
    "X"     : 3,
    "LB"    : 4,
    "RB"    : 5,
    "LT"    : 6,
    "RT"    : 7,
    "select": 8,
    "start" : 9,
    "home"  : 12
}

# Pemetaan axis analog
AXIS_MAP = {
    "axis_1_x": 0,   # Analog Kiri X
    "axis_1_y": 1,   # Analog Kiri Y
    "axis_2_x": 2,   # Analog Kanan X / atau LT di beberapa stik
    "axis_2_y": 3,   # Analog Kanan Y
    "lt"      : 4,   # Trigger Kiri  (jika berupa axis)
    "rt"      : 5,   # Trigger Kanan (jika berupa axis)
    "dpad_x"  : 6,   # D-Pad X
    "dpad_y"  : 7,   # D-Pad Y
}

DEADZONE = 0.03

# =========================
# STATE BERSAMA (Thread-safe)
# =========================
lock = threading.Lock()
seq  = 0

# State awal: semua nol
state = {
    "buttons": {name: 0 for name in BUTTON_MAP},
    "axes"   : {name: 0.0 for name in AXIS_MAP},
    "lt"     : 0.0,
    "rt"     : 0.0,
    "joystick_connected": True
}


def apply_deadzone(val, threshold=DEADZONE):
    return 0.0 if abs(val) < threshold else round(val, 4)


# =========================
# THREAD BACA EVENT STIK
# =========================
def event_reader():
    """Membaca event pygame secara real-time dan memperbarui state."""
    global state
    while True:
        for event in pygame.event.get():

            if event.type == pygame.JOYDEVICEADDED:
                with lock:
                    state["joystick_connected"] = True
                print("[INFO] Joystick tersambung kembali.")

            elif event.type == pygame.JOYDEVICEREMOVED:
                with lock:
                    state["joystick_connected"] = False
                    # Nolkan semua input saat stik terputus
                    state["buttons"] = {name: 0 for name in BUTTON_MAP}
                    state["axes"]    = {name: 0.0 for name in AXIS_MAP}
                    state["lt"]      = 0.0
                    state["rt"]      = 0.0
                print("[WARN] Joystick terputus!")

            elif event.type == pygame.JOYBUTTONDOWN:
                btn = event.button
                for name, idx in BUTTON_MAP.items():
                    if idx == btn:
                        with lock:
                            state["buttons"][name] = 1

            elif event.type == pygame.JOYBUTTONUP:
                btn = event.button
                for name, idx in BUTTON_MAP.items():
                    if idx == btn:
                        with lock:
                            state["buttons"][name] = 0

            elif event.type == pygame.JOYAXISMOTION:
                ax  = event.axis
                val = apply_deadzone(event.value)
                with lock:
                    for name, idx in AXIS_MAP.items():
                        if idx == ax:
                            state["axes"][name] = val
                    # Normalisasi Trigger LT & RT ke 0.0–1.0
                    lt_raw = state["axes"].get("lt", 0.0)
                    rt_raw = state["axes"].get("rt", 0.0)
                    state["lt"] = round((lt_raw + 1.0) / 2.0, 4)
                    state["rt"] = round((rt_raw + 1.0) / 2.0, 4)

        time.sleep(0.001)  # CPU-friendly polling


# =========================
# THREAD KIRIM HEARTBEAT
# =========================
def heartbeat_sender():
    """Mengirim paket status stik penuh setiap 20ms (50Hz)."""
    global seq
    period    = 1.0 / SEND_HZ
    next_time = time.monotonic()

    while True:
        with lock:
            snap = {
                "seq"      : seq,
                "timestamp": time.time(),
                "type"     : "heartbeat",
                "joystick_connected": state["joystick_connected"],
                "buttons"  : dict(state["buttons"]),
                "analog"   : {
                    "LT"      : state["lt"],
                    "RT"      : state["rt"],
                    "axis_1_x": state["axes"].get("axis_1_x", 0.0),
                    "axis_1_y": state["axes"].get("axis_1_y", 0.0),
                    "axis_2_x": state["axes"].get("axis_2_x", 0.0),
                    "axis_2_y": state["axes"].get("axis_2_y", 0.0),
                    "dpad_x"  : state["axes"].get("dpad_x", 0.0),
                    "dpad_y"  : state["axes"].get("dpad_y", 0.0),
                }
            }
            seq += 1

        # Kirim paket
        try:
            msg = json.dumps(snap, separators=(",", ":"))
            sock.sendto(msg.encode("utf-8"), (PC_IP, PC_PORT))
        except Exception as e:
            print(f"[ERROR] Gagal kirim UDP: {e}")

        # Jaga timing presisi 50Hz
        next_time += period
        sleep_t = next_time - time.monotonic()
        if sleep_t > 0:
            time.sleep(sleep_t)
        else:
            next_time = time.monotonic()


# =========================
# JALANKAN THREAD
# =========================
t_event = threading.Thread(target=event_reader,    daemon=True)
t_send  = threading.Thread(target=heartbeat_sender, daemon=True)
t_event.start()
t_send.start()

print("Sistem aktif — mengirim heartbeat 50Hz ke Mini PC...")
print("Tekan Ctrl+C untuk berhenti.\n")

try:
    while True:
        time.sleep(1)
        with lock:
            bt_stat = "CONNECTED" if state["joystick_connected"] else "DISCONNECTED"
        print(f"[STATUS] SEQ={seq:6d} | Joystick: {bt_stat} | "
              f"A={state['buttons'].get('A',0)} B={state['buttons'].get('B',0)} "
              f"LT={state['lt']:.2f} RT={state['rt']:.2f}")
except KeyboardInterrupt:
    print("\nProgram dihentikan.")
finally:
    sock.close()
    pygame.quit()
