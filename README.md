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

> Setelah download ZIP dan extract, buka terminal **di dalam folder hasil extract**
> (misal `GUI-MONITORING-JOYSTICK-main/`). Semua perintah `cd` di bawah relatif dari folder itu.

### 1. Raspberry Pi (pengirim)

```bash
cd raspberry_pi/
sudo apt install python3-pygame        # atau: pip install pygame (di venv)
# Edit PC_IP di API_AKI.ino sesuai IP Mini PC
python3 API_AKI.ino
```

### 2. Mini PC / Laptop (penerima + GUI)

**Linux (Ubuntu/Debian baru) — cara termudah via apt:**
```bash
cd mini_pc_gui/
sudo apt install python3-pyqt5 python3-serial
python3 main.py
```

**Linux — alternatif pakai virtual environment:**
```bash
cd mini_pc_gui/
sudo apt install python3-venv python3-full
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```
Selanjutnya cukup `source venv/bin/activate` lalu `python3 main.py`.

**Windows:**
```bat
cd mini_pc_gui
pip install -r requirements.txt
python main.py
```

> Jika muncul `error: externally-managed-environment` saat `pip install`, gunakan cara apt atau venv di atas.
> Pastikan firewall laptop mengizinkan UDP port 5005, dan laptop satu jaringan dengan Raspberry Pi.

##  Cek Format JSON Payload

`check_payload.py` dipakai untuk memastikan data yang dikirim Raspberry Pi formatnya benar,
**tanpa membuka GUI**.

**Cara kerja:**
1. Membuka socket UDP di port yang sama dengan GUI (dibaca dari `config.json`, default 5005).
2. Setiap paket yang masuk di-decode sebagai JSON. Jika gagal → ditandai **MALFORMED**.
3. Paket dikenali jenisnya: *heartbeat* (punya `buttons`), *button*, atau *axis*.
4. Isi paket diperiksa:
   - field wajib ada (`seq`, `timestamp`, `buttons`, `analog`, `joystick_connected`)
   - tipe data benar (angka, 0/1, object)
   - rentang nilai: stick & D-pad `-1.0..1.0`, LT/RT `0.0..1.0`, tombol `0/1`
   - latency wajar (`0–10000 ms`), jika tidak berarti jam RPi & PC belum sinkron
5. Tiap paket diberi status **OK** (valid), **WARN** (terbaca tapi ada yang kurang/aneh),
   atau **ERROR** (format salah), beserta ringkasan nilai stick, trigger, dan tombol yang ditekan.
6. Saat dihentikan (Ctrl+C), ditampilkan ringkasan total paket, jumlah valid/error, dan rate paket per detik.

> ⚠️ Tutup GUI dulu — keduanya memakai port UDP yang sama.

```bash
cd mini_pc_gui/
python3 check_payload.py              # port dari config.json (default 5005)
python3 check_payload.py --raw        # tampilkan juga JSON mentah
python3 check_payload.py --count 50   # berhenti setelah 50 paket
python3 check_payload.py --port 5005  # port custom
python3 check_payload.py --send-test  # kirim 1 paket contoh ke localhost (uji tanpa RPi)
```

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
