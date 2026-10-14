#  Robot AKI – Joystick Monitoring System

Sistem monitoring robot berbasis joystick dengan komunikasi UDP antara **Raspberry Pi** dan **Mini PC**, serta kontrol motor via **Teensy** melalui serial.

##  Arsitektur Sistem

```
[Joystick / Gamepad]
        │ Bluetooth
        ▼
┌─────────────────────┐       UDP JSON        ┌──────────────────────────┐      Serial      ┌─────────┐
│   Raspberry Pi      │  ──── @ 50Hz ──────►  │  Mini PC – GUI Monitoring│ ──── 115200 ───► │  Teensy │
│  raspberry_pi/      │      port 5005         │  mini_pc_gui/            │                  │  Motor  │
└─────────────────────┘                        └──────────────────────────┘                  └─────────┘
```

##  Struktur Folder

```
GUI-MONITORING-JOYSTICK/
├── raspberry_pi/          ← Script yang dijalankan di Raspberry Pi
│   ├── API_AKI.ino        ← Pengirim UDP heartbeat 50Hz (Python)
│   └── README.md
│
├── mini_pc_gui/           ← Aplikasi GUI PyQt5 yang dijalankan di Mini PC
│   ├── main.py            ← Entry point, jendela utama
│   ├── udp_receiver.py    ← Thread penerima UDP
│   ├── serial_transceiver.py  ← Thread serial ke Teensy
│   ├── gui_panels.py      ← Widget panel UI
│   ├── style_sheet.py     ← Stylesheet dark theme
│   ├── config_manager.py  ← Manajemen konfigurasi JSON
│   ├── telemetry_logger.py ← Logger telemetri
│   ├── test_sender_sim.py ← Simulator UDP untuk testing
│   ├── config.json        ← File konfigurasi
│   └── requirements.txt   ← Dependensi Python
│
└── README.md              ← Dokumen ini
```

##  Cara Menjalankan

### 1. Raspberry Pi (pengirim)

```bash
cd raspberry_pi/
pip install pygame
# Edit PC_IP di API_AKI.ino sesuai IP Mini PC
python3 API_AKI.ino
```

### 2. Mini PC (penerima + GUI)

```bash
cd mini_pc_gui/
pip install -r requirements.txt
python3 main.py
```

### Testing tanpa Raspberry Pi

```bash
cd mini_pc_gui/
python3 test_sender_sim.py   # Kirim data simulasi ke GUI
```

##  Konfigurasi

Edit `mini_pc_gui/config.json`:
```json
{
  "udp_port": 5005,
  "serial_port": "/dev/ttyACM0",
  "serial_baud": 115200
}
```

Edit `raspberry_pi/API_AKI.ino`:
```python
PC_IP   = "192.168.0.200"   # ← IP Mini PC
PC_PORT = 5005
SEND_HZ = 50
```

##  Dependensi

| Komponen | Library |
|----------|---------|
| Raspberry Pi | `pygame` ≥ 2.0 |
| Mini PC GUI | `PyQt5`, `pyserial` |

##  Author

YannSipemalas
