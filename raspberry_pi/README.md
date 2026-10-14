# Raspberry Pi – Joystick UDP Sender (API_AKI)

Script Python yang berjalan di **Raspberry Pi** untuk membaca input joystick/gamepad via Bluetooth (pygame) dan mengirimkan data ke **Mini PC** melalui UDP sebagai paket JSON dengan heartbeat **50Hz**.

## 📡 Cara Kerja

```
[Joystick / Gamepad]
       │ Bluetooth
       ▼
[Raspberry Pi]  ──── UDP JSON @ 50Hz ────►  [Mini PC : GUI Monitoring]
  API_AKI.ino                                  port 5005
```

- Mengirim paket **setiap 20ms (50Hz)** walaupun stik dalam kondisi diam (heartbeat mode)
- Status koneksi Bluetooth joystick dikirim di setiap paket (`joystick_connected`)
- Dua thread terpisah: **event reader** (realtime) + **heartbeat sender** (periodik)

## 📦 Struktur Paket UDP (JSON)

```json
{
  "seq": 1234,
  "timestamp": 1728899999.123,
  "type": "heartbeat",
  "joystick_connected": true,
  "buttons": {
    "Y": 0, "B": 0, "A": 1, "X": 0,
    "LB": 0, "RB": 0, "LT": 0, "RT": 0,
    "select": 0, "start": 0
  },
  "analog": {
    "LT": 0.0,
    "RT": 0.85,
    "axis_1_x": -0.312,
    "axis_1_y": 0.021,
    "axis_2_x": 0.0,
    "axis_2_y": 0.0,
    "dpad_x": 0.0,
    "dpad_y": 0.0
  }
}
```

## ⚙️ Konfigurasi

Edit bagian ini di `API_AKI.ino`:

```python
PC_IP   = "192.168.0.200"  # ← IP Mini PC tujuan
PC_PORT = 5005              # Port UDP
SEND_HZ = 50                # Frekuensi kirim (Hz)
DEADZONE = 0.03             # Deadzone analog stik
```

Dan sesuaikan pemetaan tombol/axis dengan jenis stik Anda:

```python
BUTTON_MAP = { "Y": 0, "B": 1, "A": 2, ... }
AXIS_MAP   = { "axis_1_x": 0, "axis_1_y": 1, ... }
```

## 🚀 Cara Menjalankan

```bash
# Install dependensi
pip install pygame

# Jalankan (pastikan joystick sudah terhubung via Bluetooth)
python3 API_AKI.ino
```

## 📋 Dependensi

| Library | Versi | Keterangan |
|---------|-------|------------|
| pygame  | ≥ 2.0 | Baca input joystick |
| socket  | stdlib | Kirim UDP |
| json    | stdlib | Encode paket |
| threading | stdlib | Multi-thread event+sender |

## 🔗 Proyek Terkait

- **GUI Monitoring**: [GUI-MONITORING-JOYSTICK](https://github.com/YannSipemalas/GUI-MONITORING-JOYSTICK) – Penerima UDP di Mini PC
