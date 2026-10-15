#  Joystick Monitoring System

Sistem monitoring robot berbasis joystick dengan komunikasi UDP antara **Raspberry Pi** dan **Mini PC**, serta kontrol motor via **Teensy** melalui serial.

##  Arsitektur Sistem

```
[Joystick / Gamepad]
        │ Bluetooth
        ▼
┌─────────────────────┐       UDP JSON        ┌──────────────────────────┐   Serial      ┌─────────┐
│   Raspberry Pi      │  ──── @ 50Hz ──────►  │  Mini PC – GUI Monitoring│ ──115200 ───► │  Teensy │
│  raspberry_pi/      │      port 5005        │  mini_pc_gui/            │               │  Motor  │
└─────────────────────┘                       └──────────────────────────┘               └─────────┘
```

##  Struktur Folder

```
GUI-MONITORING-JOYSTICK/
├── raspberry_pi/            ← Script yang dijalankan di Raspberry Pi
│   ├── API_AKI.ino          ← Pengirim UDP heartbeat 50Hz (Python)
│   └── README.md
│
├── mini_pc_gui/             ← Aplikasi GUI PyQt5 yang dijalankan di Mini PC
│   ├── main.py              ← Entry point, jendela utama
│   ├── udp_receiver.py      ← Thread penerima & parser UDP
│   ├── serial_transceiver.py← Thread serial ke Teensy
│   ├── gui_panels.py        ← Widget panel UI (tombol, trigger, analog stick)
│   ├── style_sheet.py       ← Stylesheet theme
│   ├── config_manager.py    ← Manajemen konfigurasi JSON
│   ├── telemetry_logger.py  ← Logger telemetri
│   ├── check_payload.py     ← 🆕 Tool cek/validasi format JSON payload
│   ├── config.json          ← File konfigurasi
│   └── requirements.txt     ← Dependensi Python
│
└── README.md
```

##  Fitur GUI

- Status koneksi UDP (watchdog 3 detik) & Bluetooth joystick (debounce ~3 detik)
- Indikator tombol: A, B, X, Y, LB, RB, Select, Start, Home, **L3, R3** (tekan stick)
- Bar trigger **LT / RT** (0.0 – 1.0)
- **Visualisasi analog stick kiri & kanan** — lingkaran dengan titik posisi + nilai X/Y
- Statistik jaringan: latency, jitter, packet loss, interval paket
- Diteruskan ke Teensy via serial

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

##  Cek Format JSON Payload

`check_payload.py` mendengarkan port UDP **tanpa GUI**, lalu memvalidasi setiap paket
(field wajib, tipe data, rentang nilai) dan menampilkan ringkasan per paket.

> ⚠️ Tutup GUI dulu — keduanya memakai port UDP yang sama.

```bash
cd mini_pc_gui/
python3 check_payload.py              # port dari config.json (default 5005)
python3 check_payload.py --raw        # tampilkan juga JSON mentah
python3 check_payload.py --count 50   # berhenti setelah 50 paket
python3 check_payload.py --port 5005  # port custom
python3 check_payload.py --send-test  # kirim 1 paket contoh ke localhost (uji tanpa RPi)
```

Contoh output:
```
#1     OK    heartbeat 192.168.0.10 + 20.1ms  L(+0.30,-0.70) R(+0.00,+0.00) LT=0.00 RT=0.50 BT=ON btn=A
#2     WARN  heartbeat 192.168.0.10 + 19.8ms  ...
        ! latency 35000 ms di luar 0-10000 → jam RPi & PC belum sinkron (NTP)
```
Status: `OK` = valid, `WARN` = terbaca tapi ada yang kurang, `ERROR` = format salah, `MALFORMED` = bukan JSON.

##  Format JSON Payload

### Heartbeat penuh (utama, 50Hz)
```json
{
  "type": "heartbeat",
  "seq": 1234,
  "timestamp": 1760500000.123,
  "joystick_connected": true,
  "buttons": {
    "A": 0, "B": 0, "X": 0, "Y": 0, "LB": 0, "RB": 0,
    "select": 0, "start": 0, "home": 0, "L3": 0, "R3": 0
  },
  "analog": {
    "LT": 0.0, "RT": 0.0,
    "axis_1_x": 0.0, "axis_1_y": 0.0,
    "axis_2_x": 0.0, "axis_2_y": 0.0,
    "dpad_x": 0.0, "dpad_y": 0.0
  }
}
```

| Field | Tipe | Rentang | Keterangan |
|-------|------|---------|------------|
| `seq` | int | naik terus | deteksi packet loss |
| `timestamp` | float (unix detik) | – | hitung latency (jam RPi & PC harus sinkron) |
| `joystick_connected` | bool | – | status Bluetooth gamepad |
| `buttons.*` | int | 0 / 1 | status tombol |
| `analog.LT/RT` | float | 0.0 – 1.0 | trigger |
| `analog.axis_1_x/y` | float | -1.0 – 1.0 | stick kiri (X, Y) |
| `analog.axis_2_x/y` | float | -1.0 – 1.0 | stick kanan (X, Y) |
| `analog.dpad_x/y` | float | -1.0 – 1.0 | D-pad |

### Event tunggal (opsional / legacy)
```json
{"type": "button", "button": 0, "value": 1, "seq": 1, "timestamp": 1760500000.1}
{"type": "axis",   "axis": 0,   "value": -0.5, "seq": 2, "timestamp": 1760500000.2}
```

##  Konfigurasi

Edit `mini_pc_gui/config.json` (bagian penting):
```json
{
  "network":  { "udp_listen_ip": "0.0.0.0", "udp_listen_port": 5005, "watchdog_timeout_sec": 1.0 },
  "joystick": { "deadzone_threshold": 0.05 }
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
| Mini PC GUI | `PyQt5` (atau PyQt6), `pyserial` |
| check_payload.py | hanya standard library Python 3.9+ |

##  Author

YannSipemalas
