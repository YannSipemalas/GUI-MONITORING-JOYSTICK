# 🤖 Robot System Monitoring – Mini PC Dashboard

Sistem antarmuka grafis (**GUI Desktop**) berbasis Python dan PyQt untuk monitoring input joystick dan telemetri komunikasi nirkabel robot secara *real-time*. Aplikasi ini dijalankan pada **Mini PC** untuk memantau aliran data kendali mulai dari stik joystick, perantara Raspberry Pi, hingga mikrokontroler **Teensy**.

---

## 📌 Daftar Isi
1. [Tentang Proyek](#-tentang-proyek)
2. [Arsitektur & Alur Komunikasi](#-arsitektur--alur-komunikasi)
3. [Fitur Utama](#-fitur-utama)
4. [Teknologi yang Digunakan](#-teknologi-yang-digunakan)
5. [Struktur Folder Proyek](#-struktur-folder-proyek)
6. [Instalasi & Persyaratan Sistem](#-instalasi--persyaratan-sistem)
7. [Cara Menjalankan Aplikasi](#-cara-menjalankan-aplikasi)
8. [Mode Pengujian (Simulator Mandiri)](#-mode-pengujian-simulator-mandiri)
9. [Panduan Konfigurasi (`config.json`)](#-panduan-konfigurasi-configjson)
10. [Spesifikasi Protokol Data JSON](#-spesifikasi-protokol-data-json)
11. [Penyelesaian Masalah (Troubleshooting)](#-penyelesaian-masalah-troubleshooting)
12. [Lisensi](#-lisensi)

---

## 📖 Tentang Proyek

Aplikasi ini dirancang untuk tim robotika yang membutuhkan pemantauan aliran data kendali robot secara akurat, cepat, dan transparan. Operator di Mini PC dapat memantau tombol yang ditekan, kondisi jaringan Wi-Fi, latensi paket, serta lalu lintas perintah serial ke mikrokontroler Teensy tanpa perlu memeriksa terminal setiap perangkat secara manual.

---

## 🗺️ Arsitektur & Alur Komunikasi

Sistem beroperasi melalui 3 tahapan komunikasi berantai:

```
┌─────────────────┐       Bluetooth       ┌──────────────────┐
│ Joystick / Stik │ ───────────────────>  │   Raspberry Pi   │
└─────────────────┘                       └──────────────────┘
                                                   │
                                                   │ Wi-Fi IPv4 (UDP Port 5005)
                                                   ▼
┌─────────────────┐   Serial (/dev/ttyACM0)┌──────────────────┐
│     Teensy      │ <───────────────────  │  Mini PC (GUI)   │
│ Microcontroller │  (115200 Baud @ 50Hz) └──────────────────┘
└─────────────────┘
```

| Tahap | Perangkat | Jalur Komunikasi | Peran / Fungsi |
| :---: | :--- | :--- | :--- |
| **1** | Joystick $\rightarrow$ Raspberry Pi | Bluetooth | Membaca tombol dan stik fisik menggunakan Pygame. |
| **2** | Raspberry Pi $\rightarrow$ Mini PC | Wi-Fi IPv4 (UDP 5005) | Mengirimkan paket event tombol dan analog secara nirkabel. |
| **3** | Mini PC $\rightarrow$ Teensy | Serial USB (`/dev/ttyACM0`) | Meneruskan perintah kontrol terpadu pada frekuensi 50 Hz. |

---

## ✨ Fitur Utama

- **Joystick Input Monitoring**:
  - Menampilkan status tombol (`A`, `B`, `X`, `Y`, `LB`, `RB`, `select`, `start`, `home`) dengan badge status **`PRESSED`** / **`RELEASED`** secara *real-time*.
  - Menampilkan nilai float pemicu analog `LT` dan `RT` ($0.0 - 1.0$).
- **Connection Status 3 Titik**:
  - Indikator status visual lampu hijau (`CONNECTED`) dan merah (`DISCONNECTED`) untuk:
    1. Joystick $\rightarrow$ Raspberry Pi (Bluetooth)
    2. Raspberry Pi $\rightarrow$ Mini PC (Wi-Fi IPv4 : 5005)
    3. Mini PC $\rightarrow$ Teensy (Serial)
- **Statistik Komunikasi & Integritas Paket**:
  - Menghitung `Packets Received`, `Packets Lost`, `Packet Loss (%)`, `Packet Rate (packet/s)`.
  - Pemisahan jumlah `Axis Packets`, `Button Packets`, dan deteksi `Malformed Packets`.
- **Pengukuran Latensi & Kedatangan Paket**:
  - Menghitung *Average*, *Minimum*, *Maximum Latency*, dan *Latency Jitter* dalam milidetik ($ms$).
  - Menghitung interval kedatangan paket (*Packet Arrival Interval & Jitter*).
- **Pengelolaan Serial Teensy Terpadu**:
  - Pemantauan status port (`/dev/ttyACM0`), Baudrate (`115200`), dan laju kirim (`50 Hz`).
  - Pemisahan log data yang dikirim (`[TX]`) dan data balasan umpan balik mikrokontroler (`[RX]`).
  - Fitur **Auto-Reconnect** otomatis jika kabel serial terlepas.
- **Keamanan & Safety Failsafe**:
  - **Watchdog Timer (1.0s)**: Jika koneksi nirkabel terputus lebih dari 1 detik, input stik seketika di-nolkan (*auto-zeroing*) untuk mencegah robot bergerak liar.
  - **Emergency Stop (E-Stop)**: Tombol darurat di GUI + pintasan keyboard **Spasi** untuk menghentikan seluruh perintah robot secara instan.
- **System Log & Perekam Telemetri (Blackbox CSV)**:
  - Konsol log aktivitas bersistem kategori (`[INFO]`, `[WARN]`, `[ERROR]`).
  - Tombol **`Rec CSV`** untuk merekam seluruh telemetri tombol, sumbu, dan latensi per frame ke file `.csv` di folder `./logs/`.

---

## 🛠️ Teknologi yang Digunakan

- **Bahasa Pemrograman**: [Python 3.8+](https://www.python.org/)
- **Framework Antarmuka (GUI)**: [PyQt5](https://pypi.org/project/PyQt5/) / [PyQt6](https://pypi.org/project/PyQt6/) (Mendukung kompatibilitas multi-versi otomatis)
- **Komunikasi Jaringan**: Python `socket` (UDP Non-blocking Receiver)
- **Komunikasi Serial**: [PySerial](https://pypi.org/project/pyserial/)
- **Format Data**: JSON (*JavaScript Object Notation*)

---

## 📂 Struktur Folder Proyek

Proyek ini dibangun dengan arsitektur modular yang rapi:

```
GUI_MONITORING_JOYSTICK/
├── main.py                # File utama (Entry Point) untuk menjalankan aplikasi GUI
├── config.json            # File konfigurasi IP, Port, Serial, & Thresholds
├── config_manager.py      # Modul pengelola konfigurasi & pemetaan hardware
├── udp_receiver.py        # Worker thread penerima UDP 5005 & kalkulator telemetri
├── serial_transceiver.py  # Worker thread pengirim serial Teensy 50 Hz & receiver RX
├── telemetry_logger.py    # Modul perekam telemetri time-series ke file CSV
├── gui_panels.py          # Definisi komponen kartu & tata letak 3 kolom antarmuka
├── style_sheet.py         # Tema visual QSS Clean Modern Light Theme (Putih & Biru)
├── test_sender_sim.py     # Simulator pengirim data UDP untuk pengujian mandiri
├── requirements.txt       # Daftar dependensi library Python
├── .gitignore             # Pengabaian file cache dan file rekaman log
└── README.md              # Dokumentasi lengkap repositori
```

---

## 💻 Instalasi & Persyaratan Sistem

### 1. Kloning Repositori
```bash
git clone https://github.com/username-anda/GUI_MONITORING_JOYSTICK.git
cd GUI_MONITORING_JOYSTICK
```

### 2. Pasang Dependensi
Pastikan Python 3 dan pip sudah terpasang, lalu jalankan:
```bash
pip install -r requirements.txt
```

> **Catatan Pengguna Linux (Ubuntu/Debian):**  
> Jika menggunakan Python sistem, Anda juga dapat menginstal langsung via APT:
> ```bash
> sudo apt update
> sudo apt install python3-pyqt5 python3-serial
> ```

### 3. Izin Akses Port Serial (Khusus Linux)
Agar pengguna dapat mengakses port serial `/dev/ttyACM0` tanpa memerlukan `sudo`:
```bash
sudo usermod -a -G dialout $USER
```
*(Setelah menjalankan perintah di atas, lakukan log out lalu log in kembali).*

---

## 🚀 Cara Menjalankan Aplikasi

Jalankan perintah berikut pada terminal di Mini PC:
```bash
python3 main.py
```

Antarmuka GUI akan terbuka dan otomatis mulai mendengarkan paket UDP di port `5005` serta mencari sambungan serial Teensy di `/dev/ttyACM0`.

---

## 🧪 Mode Pengujian (Simulator Mandiri)

Anda dapat menguji fungsi antarmuka GUI secara penuh **tanpa perlu menghubungkan stik fisik, Raspberry Pi, atau mikrokontroler Teensy**:

1. **Jalankan Aplikasi GUI (Terminal 1)**:
   ```bash
   python3 main.py
   ```
2. **Jalankan Simulator (Terminal 2)**:
   ```bash
   python3 test_sender_sim.py
   ```

*Simulator akan secara otomatis mengirimkan data pergerakan analog stick berputar halus, pemicu LT/RT, serta tombol A, B, X, Y yang aktif bergantian.*

---

## ⚙️ Panduan Konfigurasi (`config.json`)

Anda dapat menyesuaikan parameter perangkat tanpa perlu menyentuh kode program utama:

```json
{
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
    "invert_y_axis": false
  },
  "thresholds": {
    "packet_loss_warn_percent": 5.0,
    "latency_warn_ms": 150.0
  },
  "logging": {
    "auto_save_log": true,
    "log_directory": "./logs"
  }
}
```

- **`udp_listen_port`**: Nomor port UDP penerima (default: `5005`).
- **`watchdog_timeout_sec`**: Batas waktu deteksi hilang sinyal sebelum memicu *failsafe* (default: `1.0` detik).
- **`port`**: Alamat port serial Teensy (`/dev/ttyACM0` di Linux atau `COM3` di Windows).
- **`send_hz`**: Frekuensi pengiriman data ke Teensy (default: `50 Hz` = setiap $20 ms$).
- **`deadzone_threshold`**: Ambang batas toleransi *drift* analog stick (default: `0.05`).

---

## 📑 Spesifikasi Protokol Data JSON

### A. Format Paket UDP dari Raspberry Pi ke Mini PC

Sistem mendukung format berbasis event (*event-based*) yang dikirimkan saat ada perubahan:

* **Event Tombol:**
```json
{
  "seq": 105,
  "timestamp": 1728639201.512,
  "send_time": 4210.939,
  "type": "button",
  "button": 2,
  "value": 1
}
```
*(Nilai `button: 2` = Tombol A, `value: 1` = Pressed, `value: 0` = Released).*

* **Event Analog Stick / Trigger:**
```json
{
  "seq": 106,
  "timestamp": 1728639201.530,
  "send_time": 4210.957,
  "type": "axis",
  "axis": 0,
  "value": -0.852
}
```

---

### B. Format Paket Serial dari Mini PC ke Teensy

Dikirimkan secara periodik ($50 Hz$) diakhiri baris baru (`\n`):
```json
{
  "Analog 1 X": 0.05,
  "Analog 1 Y": -0.85,
  "Analog 2 X": 0.0,
  "Analog 2 Y": 0.0,
  "buttons": {
    "Y": 0, "B": 0, "A": 1, "X": 0,
    "LB": 0, "RB": 0, "LT": 0, "RT": 0,
    "select": 0, "start": 0, "home": 0,
    "up": 0, "down": 0, "left": 0, "right": 0
  }
}
```

---

## 🔧 Penyelesaian Masalah (Troubleshooting)

1. **`Permission denied: '/dev/ttyACM0'`**:
   - Terjadi karena akun pengguna Linux Anda belum masuk ke grup `dialout`.
   - **Solusi**: Jalankan `sudo usermod -a -G dialout $USER`, lalu restart sesi login Anda.

2. **Data Tombol Tidak Muncul di GUI**:
   - Pastikan Raspberry Pi dan Mini PC terhubung ke Wi-Fi / hotspot yang sama.
   - Periksa apakah alamat IP Mini PC yang dituju pada Raspberry Pi sudah sesuai.
   - Pastikan firewall Linux tidak memblokir UDP port 5005:
     ```bash
     sudo ufw allow 5005/udp
     ```

3. **Status Teensy Tetap `DISCONNECTED`**:
   - Periksa apakah kabel USB Teensy sudah terpasang dengan baik.
   - Cek nama port di terminal menggunakan perintah:
     ```bash
     ls /dev/ttyACM* /dev/ttyUSB*
     ```
   - Sesuaikan nama port yang terdeteksi di dalam file `config.json`.

---

## 👥 Lisensi & Kontributor

- **Pengembang**: Tim Robotika
- **Lisensi**: Proyek ini dilisensikan di bawah [MIT License](https://opensource.org/licenses/MIT).
