# -*- coding: utf-8 -*-
"""
MODUL: gui_panels.py
Fungsi: Definisi widget panel dan tata letak 3 kolom antarmuka grafis PyQt.
"""

from datetime import datetime

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
        QGridLayout, QFrame, QTextEdit
    )
except ImportError:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
        QGridLayout, QFrame, QTextEdit
    )


def align_center():
    return Qt.AlignCenter if hasattr(Qt, 'AlignCenter') else Qt.AlignmentFlag.AlignCenter


# ============================================================
# 1. HEADER BAR WIDGET
# ============================================================
class HeaderWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderCard")
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(12, 8, 12, 8)

        # Title
        title_box = QHBoxLayout()
        icon_lbl = QLabel("🤖")
        icon_lbl.setStyleSheet("font-size: 24px;")
        title_lbl = QLabel("ROBOT SYSTEM MONITORING")
        title_lbl.setObjectName("MainTitle")
        sep_lbl = QLabel("|")
        sep_lbl.setStyleSheet("color: #94A3B8; font-size: 18px; font-weight: bold; margin: 0 6px;")
        sub_title = QLabel("MINI PC")
        sub_title.setObjectName("SubTitle")

        title_box.addWidget(icon_lbl)
        title_box.addWidget(title_lbl)
        title_box.addWidget(sep_lbl)
        title_box.addWidget(sub_title)
        title_box.addStretch()
        h_layout.addLayout(title_box)

        # Right Controls: E-STOP & Clock
        right_box = QHBoxLayout()
        self.btn_estop = QPushButton("🚨 E-STOP (SPACE)")
        self.btn_estop.setObjectName("BtnEstop")
        self.btn_estop.setCursor(Qt.CursorShape.PointingHandCursor if hasattr(Qt, 'CursorShape') else Qt.PointingHandCursor)

        self.lbl_clock = QLabel(datetime.now().strftime("🕒 %Y-%m-%d %H:%M:%S"))
        self.lbl_clock.setObjectName("ClockLabel")

        right_box.addWidget(self.btn_estop)
        right_box.addSpacing(16)
        right_box.addWidget(self.lbl_clock)
        h_layout.addLayout(right_box)


# ============================================================
# 2. KOLOM 1: JOYSTICK INPUT PANEL
# ============================================================
class JoystickInputPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelCard")
        self.setFixedWidth(280)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("📄  Joystick Input")
        title.setObjectName("CardHeader")
        layout.addWidget(title)

        sub = QLabel("Button Status")
        sub.setStyleSheet("color: #64748B; font-weight: bold; font-size: 12px; margin-top: 4px;")
        layout.addWidget(sub)

        # Daftar Tombol Utama
        self.btn_badges = {}
        for btn_name in ["A", "B", "X", "Y", "LB", "RB"]:
            row = QHBoxLayout()
            b_label = QLabel(f"{btn_name:<6} :")
            b_label.setObjectName("ButtonNameLabel")
            badge = QLabel("RELEASED")
            badge.setObjectName("BadgeReleased")
            badge.setAlignment(align_center())
            self.btn_badges[btn_name] = badge
            row.addWidget(b_label)
            row.addWidget(badge)
            layout.addLayout(row)

        # Trigger LT & RT
        row_lt = QHBoxLayout()
        lbl_lt = QLabel("LT     :")
        lbl_lt.setObjectName("ButtonNameLabel")
        self.val_lt = QLabel("0.00")
        self.val_lt.setObjectName("AnalogVal")
        lbl_lt_tag = QLabel("(analog)")
        lbl_lt_tag.setStyleSheet("color: #94A3B8; font-size: 11px;")
        row_lt.addWidget(lbl_lt)
        row_lt.addWidget(self.val_lt)
        row_lt.addWidget(lbl_lt_tag)
        layout.addLayout(row_lt)

        row_rt = QHBoxLayout()
        lbl_rt = QLabel("RT     :")
        lbl_rt.setObjectName("ButtonNameLabel")
        self.val_rt = QLabel("0.00")
        self.val_rt.setObjectName("AnalogVal")
        lbl_rt_tag = QLabel("(analog)")
        lbl_rt_tag.setStyleSheet("color: #94A3B8; font-size: 11px;")
        row_rt.addWidget(lbl_rt)
        row_rt.addWidget(self.val_rt)
        row_rt.addWidget(lbl_rt_tag)
        layout.addLayout(row_rt)

        # Tombol Khusus (select, start, home)
        for btn_name in ["select", "start", "home"]:
            row = QHBoxLayout()
            b_label = QLabel(f"{btn_name:<6} :")
            b_label.setObjectName("ButtonNameLabel")
            badge = QLabel("RELEASED")
            badge.setObjectName("BadgeReleased")
            badge.setAlignment(align_center())
            self.btn_badges[btn_name] = badge
            row.addWidget(b_label)
            row.addWidget(badge)
            layout.addLayout(row)

        layout.addStretch()

        # Kotak Informasi
        info_box = QFrame()
        info_box.setObjectName("InfoBox")
        ib_layout = QHBoxLayout(info_box)
        ib_layout.setContentsMargins(8, 8, 8, 8)
        lbl_icon = QLabel("ℹ️")
        lbl_txt = QLabel("LT/RT menampilkan nilai analog (0.0 - 1.0).\nData tombol diperbarui secara real-time.")
        lbl_txt.setStyleSheet("color: #475569; font-size: 10px; line-height: 1.2;")
        ib_layout.addWidget(lbl_icon)
        ib_layout.addWidget(lbl_txt)
        layout.addWidget(info_box)

    def update_inputs(self, buttons_dict, lt_val, rt_val):
        for btn_name, val in buttons_dict.items():
            if btn_name in self.btn_badges:
                b = self.btn_badges[btn_name]
                if val:
                    b.setText("PRESSED")
                    b.setObjectName("BadgePressed")
                else:
                    b.setText("RELEASED")
                    b.setObjectName("BadgeReleased")
                b.setStyle(b.style())
        self.val_lt.setText(f"{lt_val:.2f}")
        self.val_rt.setText(f"{rt_val:.2f}")


# ============================================================
# 3. KOLOM 2: TELEMETRY & STATISTICS PANEL
# ============================================================
class TelemetryPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Connection Status
        conn_header = QLabel("🔗  Connection Status")
        conn_header.setObjectName("CardHeader")
        layout.addWidget(conn_header)

        conn_cards_layout = QHBoxLayout()
        conn_cards_layout.setSpacing(8)

        self.node_bt = self.create_node_card("📱", "Joystick → Raspberry Pi", "(Bluetooth)")
        self.node_wifi = self.create_node_card("📶", "Raspberry Pi → Mini PC", "(Wi-Fi IPv4 : 5005)")
        self.node_serial = self.create_node_card("🖧", "Mini PC → TENSY", "(Serial)")

        conn_cards_layout.addWidget(self.node_bt)
        conn_cards_layout.addWidget(self.node_wifi)
        conn_cards_layout.addWidget(self.node_serial)
        layout.addLayout(conn_cards_layout)

        # 2. Communication Statistics
        layout.addSpacing(4)
        stat_header = QLabel("📊  Communication Statistics")
        stat_header.setObjectName("CardHeader")
        layout.addWidget(stat_header)

        stat_grid = QGridLayout()
        stat_grid.setVerticalSpacing(4)
        stat_grid.setHorizontalSpacing(10)

        self.lbl_pkt_recv = QLabel("0")
        self.lbl_pkt_lost = QLabel("0")
        self.lbl_pkt_loss_pct = QLabel("0.000 %")
        self.lbl_pkt_rate = QLabel("0.00 packet/s")
        self.lbl_axis_pkt = QLabel("0")
        self.lbl_btn_pkt = QLabel("0")
        self.lbl_malformed_pkt = QLabel("0")

        self.add_stat_row(stat_grid, 0, "Packets Received", self.lbl_pkt_recv)
        self.add_stat_row(stat_grid, 1, "Packets Lost", self.lbl_pkt_lost)
        self.add_stat_row(stat_grid, 2, "Packet Loss", self.lbl_pkt_loss_pct)
        self.add_stat_row(stat_grid, 3, "Packet Rate", self.lbl_pkt_rate)
        self.add_stat_row(stat_grid, 4, "Axis Packets", self.lbl_axis_pkt)
        self.add_stat_row(stat_grid, 5, "Button Packets", self.lbl_btn_pkt)
        self.add_stat_row(stat_grid, 6, "Malformed Packets", self.lbl_malformed_pkt)
        layout.addLayout(stat_grid)

        # 3. Latency
        layout.addSpacing(4)
        lat_header = QLabel("⏱️  Latency")
        lat_header.setObjectName("CardHeader")
        layout.addWidget(lat_header)

        lat_grid = QGridLayout()
        lat_grid.setVerticalSpacing(3)
        self.lbl_lat_avg = QLabel("0.000 ms")
        self.lbl_lat_min = QLabel("0.000 ms")
        self.lbl_lat_max = QLabel("0.000 ms")
        self.lbl_lat_jit = QLabel("0.000 ms")

        self.add_stat_row(lat_grid, 0, "Average Latency", self.lbl_lat_avg)
        self.add_stat_row(lat_grid, 1, "Minimum Latency", self.lbl_lat_min)
        self.add_stat_row(lat_grid, 2, "Maximum Latency", self.lbl_lat_max)
        self.add_stat_row(lat_grid, 3, "Latency Jitter", self.lbl_lat_jit)
        layout.addLayout(lat_grid)

        # 4. Packet Arrival
        layout.addSpacing(4)
        arr_header = QLabel("📶  Packet Arrival")
        arr_header.setObjectName("CardHeader")
        layout.addWidget(arr_header)

        arr_grid = QGridLayout()
        arr_grid.setVerticalSpacing(3)
        self.lbl_arr_avg = QLabel("0.000 ms")
        self.lbl_arr_min = QLabel("0.000 ms")
        self.lbl_arr_max = QLabel("0.000 ms")
        self.lbl_arr_jit = QLabel("0.000 ms")

        self.add_stat_row(arr_grid, 0, "Average Interval", self.lbl_arr_avg)
        self.add_stat_row(arr_grid, 1, "Minimum Interval", self.lbl_arr_min)
        self.add_stat_row(arr_grid, 2, "Maximum Interval", self.lbl_arr_max)
        self.add_stat_row(arr_grid, 3, "Arrival Jitter", self.lbl_arr_jit)
        layout.addLayout(arr_grid)

    def create_node_card(self, icon, title, subtitle):
        card = QFrame()
        card.setObjectName("ConnNodeCard")
        l = QVBoxLayout(card)
        l.setContentsMargins(8, 8, 8, 8)
        l.setSpacing(3)
        l.setAlignment(align_center())

        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 18px;")
        ic.setAlignment(align_center())

        t = QLabel(title)
        t.setStyleSheet("font-size: 11px; font-weight: bold; color: #1E293B;")
        t.setAlignment(align_center())

        st = QLabel(subtitle)
        st.setStyleSheet("font-size: 10px; color: #64748B;")
        st.setAlignment(align_center())

        badge = QLabel("○  Menunggu...")
        badge.setObjectName("NodeBadgeWaiting")
        badge.setAlignment(align_center())

        l.addWidget(ic)
        l.addWidget(t)
        l.addWidget(st)
        l.addWidget(badge)

        card.badge_label = badge
        return card

    def add_stat_row(self, grid, row, name, val_widget):
        l_name = QLabel(f"{name:<22} :")
        l_name.setObjectName("StatName")
        val_widget.setObjectName("StatVal")
        grid.addWidget(l_name, row, 0)
        grid.addWidget(val_widget, row, 1)

    def update_telemetry(self, snap):
        self.lbl_pkt_recv.setText(str(snap.get("received", 0)))
        self.lbl_pkt_lost.setText(str(snap.get("lost", 0)))
        self.lbl_pkt_loss_pct.setText(f"{snap.get('loss_percent', 0.0):.3f} %")
        self.lbl_pkt_rate.setText(f"{snap.get('packet_rate', 0.0):.2f} packet/s")
        self.lbl_axis_pkt.setText(str(snap.get("axis_packets", 0)))
        self.lbl_btn_pkt.setText(str(snap.get("button_packets", 0)))
        self.lbl_malformed_pkt.setText(str(snap.get("malformed_packets", 0)))

        self.lbl_lat_avg.setText(f"{snap.get('latency_avg', 0.0):.3f} ms")
        self.lbl_lat_min.setText(f"{snap.get('latency_min', 0.0):.3f} ms")
        self.lbl_lat_max.setText(f"{snap.get('latency_max', 0.0):.3f} ms")
        self.lbl_lat_jit.setText(f"{snap.get('latency_jitter', 0.0):.3f} ms")

        self.lbl_arr_avg.setText(f"{snap.get('arrival_avg', 0.0):.3f} ms")
        self.lbl_arr_min.setText(f"{snap.get('arrival_min', 0.0):.3f} ms")
        self.lbl_arr_max.setText(f"{snap.get('arrival_max', 0.0):.3f} ms")
        self.lbl_arr_jit.setText(f"{snap.get('arrival_jitter', 0.0):.3f} ms")


# ============================================================
# 4. KOLOM 3: TEENSY SERIAL & LOG PANEL
# ============================================================
class TeensyLogPanel(QFrame):
    def __init__(self, serial_cfg, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Teensy Status
        head_row = QHBoxLayout()
        title = QLabel("🖧  TENSY Serial")
        title.setObjectName("CardHeader")
        self.badge_status = QLabel("○  Menunggu...")
        self.badge_status.setObjectName("BadgeStatusWaiting")

        head_row.addWidget(title)
        head_row.addStretch()
        head_row.addWidget(self.badge_status)
        layout.addLayout(head_row)

        info_grid = QGridLayout()
        info_grid.setVerticalSpacing(3)
        self.lbl_st = QLabel("Menunggu...")
        self.lbl_st.setStyleSheet("color: #94A3B8; font-weight: bold;")
        self.lbl_port = QLabel(serial_cfg.get("port", "/dev/ttyACM0"))
        self.lbl_baud = QLabel(str(serial_cfg.get("baudrate", 115200)))
        self.lbl_hz = QLabel(f"{serial_cfg.get('send_hz', 50)} Hz")

        self.add_info_row(info_grid, 0, "Status", self.lbl_st)
        self.add_info_row(info_grid, 1, "Port", self.lbl_port)
        self.add_info_row(info_grid, 2, "Baudrate", self.lbl_baud)
        self.add_info_row(info_grid, 3, "Send Rate", self.lbl_hz)
        layout.addLayout(info_grid)

        # 2. Serial Output
        layout.addSpacing(4)
        lbl_serial_out = QLabel(">_ Serial Output (TX / RX)")
        lbl_serial_out.setObjectName("SubCardHeader")
        layout.addWidget(lbl_serial_out)

        self.txt_serial = QTextEdit()
        self.txt_serial.setObjectName("SerialConsole")
        self.txt_serial.setReadOnly(True)
        self.txt_serial.setFixedHeight(85)
        self.txt_serial.setPlaceholderText("Waiting for connection...")
        layout.addWidget(self.txt_serial)

        # 3. System Log
        layout.addSpacing(4)
        log_head = QHBoxLayout()
        lbl_log = QLabel("📋  System Log")
        lbl_log.setObjectName("SubCardHeader")
        self.btn_rec = QPushButton("● Rec CSV")
        self.btn_rec.setObjectName("BtnSmall")
        self.btn_clear = QPushButton("Clear Log")
        self.btn_clear.setObjectName("BtnSmall")

        log_head.addWidget(lbl_log)
        log_head.addStretch()
        log_head.addWidget(self.btn_rec)
        log_head.addWidget(self.btn_clear)
        layout.addLayout(log_head)

        self.txt_log = QTextEdit()
        self.txt_log.setObjectName("LogConsole")
        self.txt_log.setReadOnly(True)
        layout.addWidget(self.txt_log, stretch=1)

    def add_info_row(self, grid, row, name, val_widget):
        l_name = QLabel(f"{name:<22} :")
        l_name.setObjectName("StatName")
        val_widget.setObjectName("StatVal")
        grid.addWidget(l_name, row, 0)
        grid.addWidget(val_widget, row, 1)

    def update_serial_status(self, is_conn):
        if is_conn:
            self.lbl_st.setText("CONNECTED")
            self.lbl_st.setStyleSheet("color: #16A34A; font-weight: bold;")
            self.badge_status.setText("● CONNECTED")
            self.badge_status.setObjectName("BadgeStatusConn")
        else:
            self.lbl_st.setText("DISCONNECTED")
            self.lbl_st.setStyleSheet("color: #EF4444; font-weight: bold;")
            self.badge_status.setText("● DISCONNECTED")
            self.badge_status.setObjectName("BadgeStatusDisconn")
        self.badge_status.setStyle(self.badge_status.style())

    def append_serial_text(self, text):
        self.txt_serial.append(text)
        if len(self.txt_serial.toPlainText()) > 10000:
            self.txt_serial.clear()

    def append_log_html(self, html_entry):
        self.txt_log.append(html_entry)


# ============================================================
# 5. FOOTER BAR WIDGET
# ============================================================
class FooterWidget(QHBoxLayout):
    def __init__(self, parent=None):
        super().__init__()
        self.lbl_status = QLabel("● System Running | Mini PC | Watchdog: 1.0s")
        self.lbl_status.setStyleSheet("color: #64748B; font-size: 11px;")
        lbl_ver = QLabel("ROBOT SYSTEM MONITORING v1.0")
        lbl_ver.setStyleSheet("color: #94A3B8; font-size: 11px;")

        self.addWidget(self.lbl_status)
        self.addStretch()
        self.addWidget(lbl_ver)
