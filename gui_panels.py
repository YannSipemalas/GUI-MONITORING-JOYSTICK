#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui_panels.py – Panel-panel UI untuk GUI Monitoring Joystick.
Menampilkan:
  • Status koneksi (UDP + Bluetooth + Serial)
  • Joystick input: tombol, analog stick 1 & 2 (XY pad), LT/RT, D-Pad
  • Telemetri motor dari Teensy
  • System Log
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QProgressBar, QTextEdit, QPushButton,
    QSizePolicy, QGroupBox
)
from PyQt5.QtCore  import Qt, QPointF, QRectF
from PyQt5.QtGui   import QPainter, QColor, QPen, QFont, QBrush


# ─────────────────────────────────────────────────────────────
#  WIDGET: Joystick XY Pad (tampilan posisi analog stick)
# ─────────────────────────────────────────────────────────────
class JoystickPad(QWidget):
    """Menampilkan posisi X/Y satu analog stick sebagai titik di lingkaran."""

    def __init__(self, label: str = "", parent=None):
        super().__init__(parent)
        self.label  = label
        self.x_val  = 0.0   # −1.0 … 1.0
        self.y_val  = 0.0
        self.setFixedSize(110, 110)

    def set_values(self, x: float, y: float):
        self.x_val = max(-1.0, min(1.0, x))
        self.y_val = max(-1.0, min(1.0, y))
        self.update()

    def paintEvent(self, _event):
        p   = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy, r = w / 2, h / 2, min(w, h) / 2 - 6

        # Lingkaran luar
        p.setPen(QPen(QColor("#455a64"), 2))
        p.setBrush(QBrush(QColor("#1e272e")))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Garis silang tengah
        p.setPen(QPen(QColor("#37474f"), 1))
        p.drawLine(int(cx - r), int(cy), int(cx + r), int(cy))
        p.drawLine(int(cx), int(cy - r), int(cx), int(cy + r))

        # Titik posisi stik
        dot_x = cx + self.x_val * (r - 8)
        dot_y = cy + self.y_val * (r - 8)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#26c6da")))
        p.drawEllipse(QPointF(dot_x, dot_y), 9, 9)

        # Label
        if self.label:
            p.setPen(QColor("#b0bec5"))
            p.setFont(QFont("Inter", 8))
            p.drawText(QRectF(0, h - 16, w, 16), Qt.AlignCenter, self.label)


# ─────────────────────────────────────────────────────────────
#  WIDGET: Indikator tombol
# ─────────────────────────────────────────────────────────────
class ButtonIndicator(QLabel):
    COLOR_OFF = "#1e272e"
    COLOR_ON  = "#26c6da"
    TXT_OFF   = "#546e7a"
    TXT_ON    = "#ffffff"

    def __init__(self, label: str, parent=None):
        super().__init__(label, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(48, 30)
        self._active = False
        self._apply()

    def set_active(self, active: bool):
        if self._active != active:
            self._active = active
            self._apply()

    def _apply(self):
        bg  = self.COLOR_ON  if self._active else self.COLOR_OFF
        txt = self.TXT_ON    if self._active else self.TXT_OFF
        bdr = "#26c6da"      if self._active else "#37474f"
        self.setStyleSheet(
            f"background:{bg}; color:{txt}; border:1px solid {bdr};"
            f"border-radius:6px; font-weight:{'bold' if self._active else 'normal'};"
            f"font-size:11px;"
        )


# ─────────────────────────────────────────────────────────────
#  PANEL: Status Koneksi
# ─────────────────────────────────────────────────────────────
class ConnectionPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Status Koneksi", parent)
        self.setStyleSheet(GROUP_STYLE)

        grid = QGridLayout()
        grid.setSpacing(8)

        self._labels: dict[str, QLabel] = {}

        items = [
            ("udp",        "UDP Link",        0, 0),
            ("bluetooth",  "Bluetooth Stik",  0, 1),
            ("serial",     "Serial Teensy",   1, 0),
            ("heartbeat",  "Heartbeat",        1, 1),
        ]
        for key, name, row, col in items:
            vbox  = QVBoxLayout()
            title = QLabel(name)
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet("color:#78909c; font-size:10px;")

            val = QLabel("—")
            val.setAlignment(Qt.AlignCenter)
            val.setStyleSheet("color:#546e7a; font-weight:bold; font-size:13px;")
            val.setMinimumWidth(110)

            self._labels[key] = val
            vbox.addWidget(title)
            vbox.addWidget(val)
            frame = QFrame()
            frame.setLayout(vbox)
            frame.setStyleSheet(
                "background:#1a2330; border:1px solid #263238; border-radius:8px; padding:4px;"
            )
            grid.addWidget(frame, row, col)

        self.setLayout(grid)

    def update_status(self, key: str, status: str):
        lbl = self._labels.get(key)
        if lbl is None:
            return
        color = "#4caf50" if status == "CONNECTED" or status == "OPEN" \
               else ("#f44336" if status == "DISCONNECTED" or status == "CLOSED" or status == "ERROR"
               else "#ffa726")
        lbl.setText(status)
        lbl.setStyleSheet(
            f"color:{color}; font-weight:bold; font-size:13px;"
        )


# ─────────────────────────────────────────────────────────────
#  PANEL: Input Joystick
# ─────────────────────────────────────────────────────────────
class JoystickPanel(QGroupBox):
    BUTTONS = ["Y", "B", "A", "X", "LB", "RB", "LT", "RT", "select", "start"]

    def __init__(self, parent=None):
        super().__init__("Input Joystick", parent)
        self.setStyleSheet(GROUP_STYLE)

        root = QVBoxLayout()
        root.setSpacing(10)

        # ── Tombol Digital ──
        btn_title = QLabel("Tombol Digital")
        btn_title.setStyleSheet("color:#78909c; font-size:10px; font-weight:bold;")
        root.addWidget(btn_title)

        btn_grid  = QGridLayout()
        btn_grid.setSpacing(6)
        self._btn_indicators: dict[str, ButtonIndicator] = {}

        for i, name in enumerate(self.BUTTONS):
            ind = ButtonIndicator(name)
            self._btn_indicators[name] = ind
            btn_grid.addWidget(ind, i // 5, i % 5)

        root.addLayout(btn_grid)

        # ── Analog Sticks ──
        stick_row = QHBoxLayout()
        stick_row.setSpacing(16)

        self._pad_l = JoystickPad("L-Stick (1)")
        self._pad_r = JoystickPad("R-Stick (2)")

        for pad in (self._pad_l, self._pad_r):
            wrapper = QVBoxLayout()
            wrapper.setAlignment(Qt.AlignCenter)
            wrapper.addWidget(pad)
            stick_row.addLayout(wrapper)

        # Nilai teks X/Y
        val_grid = QGridLayout()
        val_grid.setSpacing(4)
        self._axis_labels: dict[str, QLabel] = {}
        for row_i, (key, txt) in enumerate([
            ("axis_1_x", "L-X"), ("axis_1_y", "L-Y"),
            ("axis_2_x", "R-X"), ("axis_2_y", "R-Y"),
        ]):
            title = QLabel(txt + ":")
            title.setStyleSheet("color:#78909c; font-size:10px;")
            val   = QLabel("0.000")
            val.setStyleSheet("color:#e0e0e0; font-size:11px; font-family:monospace;")
            self._axis_labels[key] = val
            val_grid.addWidget(title, row_i, 0)
            val_grid.addWidget(val,   row_i, 1)

        combined = QHBoxLayout()
        combined.addLayout(stick_row)
        combined.addSpacing(12)
        combined.addLayout(val_grid)
        combined.addStretch()
        root.addLayout(combined)

        # ── LT / RT Trigger ──
        trig_title = QLabel("Trigger (LT / RT)")
        trig_title.setStyleSheet("color:#78909c; font-size:10px; font-weight:bold;")
        root.addWidget(trig_title)

        trig_row = QHBoxLayout()
        self._lt_bar = self._make_bar("LT")
        self._rt_bar = self._make_bar("RT")
        trig_row.addLayout(self._lt_bar[0])
        trig_row.addSpacing(12)
        trig_row.addLayout(self._rt_bar[0])
        trig_row.addStretch()
        root.addLayout(trig_row)

        # ── D-Pad ──
        dpad_title = QLabel("D-Pad")
        dpad_title.setStyleSheet("color:#78909c; font-size:10px; font-weight:bold;")
        root.addWidget(dpad_title)

        dpad_row = QHBoxLayout()
        self._dpad_labels: dict[str, QLabel] = {}
        for key in ("dpad_x", "dpad_y"):
            lbl = QLabel(f"{key}: 0.0")
            lbl.setStyleSheet("color:#e0e0e0; font-size:11px; font-family:monospace;")
            self._dpad_labels[key] = lbl
            dpad_row.addWidget(lbl)
            dpad_row.addSpacing(12)
        dpad_row.addStretch()
        root.addLayout(dpad_row)

        self.setLayout(root)

    def _make_bar(self, name: str):
        vbox  = QVBoxLayout()
        label = QLabel(f"{name}: 0.00")
        label.setStyleSheet("color:#e0e0e0; font-size:11px; font-family:monospace;")
        bar   = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setFixedWidth(140)
        bar.setFixedHeight(14)
        bar.setTextVisible(False)
        bar.setStyleSheet(
            "QProgressBar{background:#1a2330; border:1px solid #37474f; border-radius:4px;}"
            "QProgressBar::chunk{background:#26c6da; border-radius:3px;}"
        )
        vbox.addWidget(label)
        vbox.addWidget(bar)
        return vbox, label, bar

    # ── Update dari data UDP ──
    def update_data(self, data: dict):
        buttons = data.get("buttons", {})
        analog  = data.get("analog",  {})

        # Tombol
        for name, ind in self._btn_indicators.items():
            ind.set_active(bool(buttons.get(name, 0)))

        # Analog sticks
        lx = analog.get("axis_1_x", 0.0)
        ly = analog.get("axis_1_y", 0.0)
        rx = analog.get("axis_2_x", 0.0)
        ry = analog.get("axis_2_y", 0.0)

        self._pad_l.set_values(lx, ly)
        self._pad_r.set_values(rx, ry)

        for key, val in [
            ("axis_1_x", lx), ("axis_1_y", ly),
            ("axis_2_x", rx), ("axis_2_y", ry)
        ]:
            self._axis_labels[key].setText(f"{val:+.3f}")

        # LT / RT
        lt = max(0.0, min(1.0, analog.get("LT", 0.0)))
        rt = max(0.0, min(1.0, analog.get("RT", 0.0)))
        _, lt_lbl, lt_bar = self._lt_bar
        _, rt_lbl, rt_bar = self._rt_bar
        lt_lbl.setText(f"LT: {lt:.2f}")
        rt_lbl.setText(f"RT: {rt:.2f}")
        lt_bar.setValue(int(lt * 100))
        rt_bar.setValue(int(rt * 100))

        # D-Pad
        for key in ("dpad_x", "dpad_y"):
            v = analog.get(key, 0.0)
            self._dpad_labels[key].setText(f"{key}: {v:+.1f}")


# ─────────────────────────────────────────────────────────────
#  PANEL: Telemetri Motor
# ─────────────────────────────────────────────────────────────
class TelemetryPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Telemetri Motor (Teensy)", parent)
        self.setStyleSheet(GROUP_STYLE)

        grid = QGridLayout()
        grid.setSpacing(8)

        self._fields: dict[str, QLabel] = {}
        items = [
            ("motor_l", "Motor Kiri"),
            ("motor_r", "Motor Kanan"),
            ("rpm_l",   "RPM Kiri"),
            ("rpm_r",   "RPM Kanan"),
            ("current", "Arus (A)"),
            ("voltage", "Tegangan (V)"),
        ]
        for i, (key, name) in enumerate(items):
            title = QLabel(name + ":")
            title.setStyleSheet("color:#78909c; font-size:10px;")
            val = QLabel("—")
            val.setStyleSheet("color:#e0e0e0; font-size:12px; font-family:monospace;")
            self._fields[key] = val
            grid.addWidget(title, i // 2, (i % 2) * 2)
            grid.addWidget(val,   i // 2, (i % 2) * 2 + 1)

        self.setLayout(grid)

    def update_telemetry(self, tele: dict):
        for key, lbl in self._fields.items():
            v = tele.get(key)
            if v is not None:
                lbl.setText(str(v))


# ─────────────────────────────────────────────────────────────
#  PANEL: System Log
# ─────────────────────────────────────────────────────────────
class LogPanel(QGroupBox):
    MAX_LINES = 200

    def __init__(self, parent=None):
        super().__init__("System Log", parent)
        self.setStyleSheet(GROUP_STYLE)

        vbox = QVBoxLayout()

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setStyleSheet(
            "background:#0d1117; color:#90a4ae; font-family:monospace; "
            "font-size:11px; border:none;"
        )
        self._text.setMinimumHeight(120)

        clear_btn = QPushButton("Bersihkan")
        clear_btn.setFixedHeight(26)
        clear_btn.setStyleSheet(
            "QPushButton{background:#1a2330; color:#78909c; border:1px solid #37474f;"
            "border-radius:4px; font-size:11px;}"
            "QPushButton:hover{background:#263238; color:#e0e0e0;}"
        )
        clear_btn.clicked.connect(self._text.clear)

        vbox.addWidget(self._text)
        vbox.addWidget(clear_btn, alignment=Qt.AlignRight)
        self.setLayout(vbox)

        self._last_msg = ""

    def append(self, msg: str):
        """Tambah baris ke log (filter duplikat berurutan)."""
        if msg == self._last_msg:
            return
        self._last_msg = msg
        self._text.append(msg)
        # Batasi jumlah baris
        doc = self._text.document()
        while doc.blockCount() > self.MAX_LINES:
            cursor = self._text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
        self._text.moveCursor(self._text.textCursor().End)


# ─────────────────────────────────────────────────────────────
#  PANEL: E-Stop
# ─────────────────────────────────────────────────────────────
class EStopPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)

        self.btn = QPushButton("🛑  E-STOP")
        self.btn.setFixedHeight(44)
        self.btn.setCheckable(True)
        self._update_style(False)
        self.btn.toggled.connect(self._update_style)
        hbox.addWidget(self.btn)
        self.setLayout(hbox)

    def _update_style(self, checked: bool):
        if checked:
            self.btn.setText("🛑  E-STOP AKTIF — klik untuk Reset")
            self.btn.setStyleSheet(
                "QPushButton{background:#b71c1c; color:white; font-size:14px;"
                "font-weight:bold; border:2px solid #ef5350; border-radius:8px;}"
                "QPushButton:hover{background:#c62828;}"
            )
        else:
            self.btn.setText("🛑  E-STOP")
            self.btn.setStyleSheet(
                "QPushButton{background:#263238; color:#ef5350; font-size:14px;"
                "font-weight:bold; border:2px solid #b71c1c; border-radius:8px;}"
                "QPushButton:hover{background:#1a2330; color:#f44336;}"
            )

    def is_active(self) -> bool:
        return self.btn.isChecked()


# ─────────────────────────────────────────────────────────────
#  SHARED STYLE
# ─────────────────────────────────────────────────────────────
GROUP_STYLE = """
QGroupBox {
    background: #151f2b;
    border: 1px solid #1e2d3e;
    border-radius: 10px;
    margin-top: 18px;
    padding: 10px;
    color: #90a4ae;
    font-size: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    top: 2px;
    color: #546e7a;
    font-size: 11px;
    font-weight: normal;
}
"""
