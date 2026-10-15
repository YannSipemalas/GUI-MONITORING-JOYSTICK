# -*- coding: utf-8 -*-
"""
MODUL: udp_receiver.py
Fungsi: Worker thread penerima paket jaringan UDP (Port 5005) & kalkulasi telemetri.
"""

import socket
import json
import time
import threading

try:
    from PyQt5.QtCore import QThread, pyqtSignal
except ImportError:
    from PyQt6.QtCore import QThread, pyqtSignal

from config_manager import BUTTON_NAMES, AXIS_MAP


class UdpReceiverWorker(QThread):
    telemetry_updated = pyqtSignal(dict)
    log_event = pyqtSignal(str, str)            # (level, message)
    connection_changed = pyqtSignal(str, bool)  # (device, is_connected)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.running = True
        self.sock = None
        self.lock = threading.Lock()

        # Metrik Telemetri
        self.packet_received = 0
        self.packet_lost = 0
        self.axis_packets = 0
        self.button_packets = 0
        self.unknown_packets = 0
        self.malformed_packets = 0
        self.last_seq = None

        self.last_packet_time = None
        self.inter_arrivals = []
        self.latencies = []

        # Status Joystick Terkini
        self.buttons = {name: 0 for name in ["A", "B", "X", "Y", "LB", "RB", "select", "start", "home", "L3", "R3"]}
        self.lt_val = 0.0
        self.rt_val = 0.0
        self.analog_axes = {0: 0.0, 1: 0.0, 3: 0.0, 4: 0.0, 6: 0.0, 7: 0.0}

        # Pelacak Packet Rate
        self.last_rate_time = time.monotonic()
        self.last_rate_count = 0
        self.current_packet_rate = 0.0

        # State koneksi — mencegah flip-flop status di UI
        # None = belum pernah emit sama sekali
        self._wifi_state   = None   # True / False / None
        self._bt_state     = None   # True / False / None
        # Debounce Bluetooth: hanya emit DISCONNECTED setelah N paket
        # berturut-turut dengan joystick_connected=False (~3 detik @ 50Hz)
        self._bt_false_streak = 0
        self.BT_DISCONNECT_THRESHOLD = 150  # paket @ 50Hz = 3 detik

    def calculate_jitter(self, values):
        if len(values) < 2:
            return 0.0
        diffs = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
        return sum(diffs) / len(diffs) if diffs else 0.0

    def run(self):
        ip = self.cfg["network"].get("udp_listen_ip", "0.0.0.0")
        port = self.cfg["network"].get("udp_listen_port", 5005)
        buf_size = self.cfg["network"].get("buffer_size", 4096)
        deadzone = self.cfg["joystick"].get("deadzone_threshold", 0.05)
        # Toleransi watchdog: disconnect hanya setelah 3.0 detik tanpa paket
        # (lebih panjang dari default 1.0s agar tahan micro-jitter Wi-Fi)
        watchdog_timeout = max(self.cfg["network"].get("watchdog_timeout_sec", 1.0), 3.0)

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((ip, port))
            self.sock.settimeout(0.5)
            self.log_event.emit("INFO", f"Socket UDP aktif di {ip}:{port}")
        except Exception as e:
            self.log_event.emit("ERROR", f"Gagal membuka port UDP {port}: {e}")
            return

        while self.running:
            try:
                data, addr = self.sock.recvfrom(buf_size)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.log_event.emit("ERROR", f"Socket UDP error: {e}")
                break

            now = time.monotonic()
            unix_now = time.time()

            try:
                msg_str = data.decode("utf-8").strip()
                pkt = json.loads(msg_str)
            except Exception:
                with self.lock:
                    self.malformed_packets += 1
                self.log_event.emit("WARN", f"Paket malformed diterima dari {addr[0]}")
                continue

            with self.lock:
                self.packet_received += 1
                pkt_type = pkt.get("type", "")

                # 1. Packet Arrival Interval
                if self.last_packet_time is not None:
                    interval = (now - self.last_packet_time) * 1000.0
                    self.inter_arrivals.append(interval)
                    if len(self.inter_arrivals) > 500:
                        self.inter_arrivals.pop(0)
                self.last_packet_time = now

                # 2. Sequence Number & Packet Loss Detection
                seq = pkt.get("seq")
                if seq is not None:
                    try:
                        seq_int = int(seq)
                        if self.last_seq is not None and seq_int > self.last_seq + 1:
                            lost_cnt = seq_int - self.last_seq - 1
                            self.packet_lost += lost_cnt
                        self.last_seq = max(self.last_seq if self.last_seq is not None else seq_int, seq_int)
                    except (ValueError, TypeError):
                        pass

                # 3. Latency Calculation
                ts = pkt.get("timestamp")
                if ts is not None:
                    try:
                        lat = (unix_now - float(ts)) * 1000.0
                        if 0 <= lat < 10000:
                            self.latencies.append(lat)
                            if len(self.latencies) > 500:
                                self.latencies.pop(0)
                    except (ValueError, TypeError):
                        pass

                # 4. Parsing Input Joystick
                if pkt_type == "button":
                    self.button_packets += 1
                    btn_idx = pkt.get("button")
                    val = int(pkt.get("value", 0))
                    if btn_idx in BUTTON_NAMES:
                        b_name = BUTTON_NAMES[btn_idx]
                        if b_name in ["LT", "RT"]:
                            if b_name == "LT": self.lt_val = 1.0 if val else 0.0
                            if b_name == "RT": self.rt_val = 1.0 if val else 0.0
                        else:
                            self.buttons[b_name] = val
                        state_str = "pressed" if val else "released"
                        self.log_event.emit("INFO", f"Button {b_name} {state_str}")

                elif pkt_type == "axis":
                    self.axis_packets += 1
                    ax_idx = pkt.get("axis")
                    raw_val = float(pkt.get("value", 0.0))
                    val = 0.0 if abs(raw_val) < deadzone else raw_val

                    if ax_idx is not None:
                        ax_int = int(ax_idx)
                        self.analog_axes[ax_int] = val

                        # Trigger LT (axis 2) & RT (axis 5)
                        if ax_int == 2:
                            self.lt_val = max(0.0, min(1.0, (val + 1.0) / 2.0 if val < 0 else val))
                        elif ax_int == 5:
                            self.rt_val = max(0.0, min(1.0, (val + 1.0) / 2.0 if val < 0 else val))

                elif "buttons" in pkt and isinstance(pkt["buttons"], dict):
                    # Format Heartbeat Penuh (dari raspberry_pi/API_AKI.ino)
                    # Paket dikirim setiap 20ms (50Hz) oleh Raspberry Pi.
                    self.button_packets += 1

                    # Update tombol + log jika ada perubahan
                    for k, v in pkt["buttons"].items():
                        if k in self.buttons:
                            new_val = int(v)
                            if new_val != self.buttons[k]:
                                state_str = "pressed" if new_val else "released"
                                self.log_event.emit("INFO", f"Button {k} {state_str}")
                            self.buttons[k] = new_val

                    # Update analog: LT, RT, dan sumbu analog stick
                    if "analog" in pkt and isinstance(pkt["analog"], dict):
                        an = pkt["analog"]
                        self.lt_val = float(an.get("LT", 0.0))
                        self.rt_val = float(an.get("RT", 0.0))
                        # Simpan sumbu analog (axis_1_x, axis_1_y, dll) ke analog_axes
                        # menggunakan index numerik agar kompatibel dengan build_teensy_packet
                        self.analog_axes[1] = float(an.get("axis_1_x", 0.0))
                        self.analog_axes[0] = float(an.get("axis_1_y", 0.0))
                        self.analog_axes[4] = float(an.get("axis_2_x", 0.0))
                        self.analog_axes[3] = float(an.get("axis_2_y", 0.0))
                        self.analog_axes[6] = float(an.get("dpad_x", 0.0))
                        self.analog_axes[7] = float(an.get("dpad_y", 0.0))

                    # Status koneksi Bluetooth joystick — dengan debounce
                    # CONNECTED: langsung, begitu joystick_connected=True
                    # DISCONNECTED: hanya setelah ~3 detik berturut-turut False
                    bt_ok = bool(pkt.get("joystick_connected", True))
                    if bt_ok:
                        # Joystick aktif → reset streak, langsung CONNECTED
                        self._bt_false_streak = 0
                        if self._bt_state is not True:
                            self._bt_state = True
                            self.connection_changed.emit("bluetooth", True)
                    else:
                        # Joystick mungkin mati → hitung streak dulu
                        self._bt_false_streak += 1
                        if self._bt_false_streak >= self.BT_DISCONNECT_THRESHOLD:
                            if self._bt_state is not False:
                                self._bt_state = False
                                self.connection_changed.emit("bluetooth", False)

                else:
                    self.unknown_packets += 1

                # Hitung Packet Rate
                t_diff = now - self.last_rate_time
                if t_diff >= 1.0:
                    self.current_packet_rate = (self.packet_received - self.last_rate_count) / t_diff
                    self.last_rate_count = self.packet_received
                    self.last_rate_time = now

                # Kalkulasi Statistik Akhir
                tot = self.packet_received + self.packet_lost
                loss_pct = (self.packet_lost / tot * 100.0) if tot > 0 else 0.0

                lat_avg = (sum(self.latencies) / len(self.latencies)) if self.latencies else 0.0
                lat_min = min(self.latencies) if self.latencies else 0.0
                lat_max = max(self.latencies) if self.latencies else 0.0
                lat_jit = self.calculate_jitter(self.latencies)

                arr_avg = (sum(self.inter_arrivals) / len(self.inter_arrivals)) if self.inter_arrivals else 0.0
                arr_min = min(self.inter_arrivals) if self.inter_arrivals else 0.0
                arr_max = max(self.inter_arrivals) if self.inter_arrivals else 0.0
                arr_jit = self.calculate_jitter(self.inter_arrivals)

                snap = {
                    "received": self.packet_received,
                    "lost": self.packet_lost,
                    "loss_percent": loss_pct,
                    "packet_rate": self.current_packet_rate,
                    "axis_packets": self.axis_packets,
                    "button_packets": self.button_packets,
                    "unknown_packets": self.unknown_packets,
                    "malformed_packets": self.malformed_packets,
                    "latency_avg": lat_avg,
                    "latency_min": lat_min,
                    "latency_max": lat_max,
                    "latency_jitter": lat_jit,
                    "arrival_avg": arr_avg,
                    "arrival_min": arr_min,
                    "arrival_max": arr_max,
                    "arrival_jitter": arr_jit,
                    "buttons": dict(self.buttons),
                    "lt": self.lt_val,
                    "rt": self.rt_val,
                    "axes": dict(self.analog_axes),
                    "last_timestamp": now
                }

            self.telemetry_updated.emit(snap)

            # ── Emit WiFi CONNECTED hanya saat state benar-benar berubah ──
            # (tidak setiap paket agar UI tidak update 50x per detik)
            if self._wifi_state is not True:
                self._wifi_state = True
                self.connection_changed.emit("wifi", True)

            # ── Bluetooth: emit hanya jika paket bukan heartbeat ──
            # (untuk heartbeat, sudah di-handle dengan debounce di blok parsing)
            if pkt_type not in ("heartbeat", "") and "buttons" not in pkt:
                if self._bt_state is not True:
                    self._bt_state = True
                    self.connection_changed.emit("bluetooth", True)

        if self.sock:
            self.sock.close()

    def reset_to_zero(self):
        """Mereset seluruh input joystick ke nilai 0 (Failsafe Safe-State)."""
        with self.lock:
            for k in self.buttons:
                self.buttons[k] = 0
            self.lt_val = 0.0
            self.rt_val = 0.0
            for k in self.analog_axes:
                self.analog_axes[k] = 0.0

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
