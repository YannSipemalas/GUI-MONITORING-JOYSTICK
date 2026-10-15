#!/usr/bin/env python3
"""
check_payload.py — Cek & validasi format JSON payload UDP dari Raspberry Pi.

Jalankan TANPA GUI (tutup GUI dulu, karena port UDP yang sama dipakai):

    python3 check_payload.py                 # listen di port dari config.json
    python3 check_payload.py --port 5005     # port custom
    python3 check_payload.py --raw           # tampilkan JSON mentah (pretty)
    python3 check_payload.py --count 20      # berhenti setelah 20 paket
    python3 check_payload.py --send-test     # kirim 1 paket contoh ke localhost

Format yang didukung (sama dengan udp_receiver.py):
  1. Heartbeat penuh : {"type":"heartbeat","seq":..,"timestamp":..,
                        "joystick_connected":true,
                        "buttons":{"A":0,...},
                        "analog":{"LT":0.0,"RT":0.0,"axis_1_x":..,"axis_1_y":..,
                                  "axis_2_x":..,"axis_2_y":..,"dpad_x":..,"dpad_y":..}}
  2. Event tombol    : {"type":"button","button":0,"value":1,"seq":..,"timestamp":..}
  3. Event axis      : {"type":"axis","axis":0,"value":-0.5,"seq":..,"timestamp":..}
"""
import argparse
import json
import os
import socket
import sys
import time

EXPECTED_BUTTONS = ["A", "B", "X", "Y", "LB", "RB",
                    "select", "start", "home", "L3", "R3"]
EXPECTED_ANALOG = ["LT", "RT", "axis_1_x", "axis_1_y",
                   "axis_2_x", "axis_2_y", "dpad_x", "dpad_y"]

G, Y, R, C, D, X = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[2m", "\033[0m"


def load_port():
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "config.json")) as f:
            return int(json.load(f)["network"].get("udp_listen_port", 5005))
    except Exception:
        return 5005


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate(pkt):
    """Return (jenis, list_error, list_warning)."""
    err, warn = [], []
    if not isinstance(pkt, dict):
        return "?", ["Root JSON bukan object {}"], warn

    for k in ("seq", "timestamp"):
        if k not in pkt:
            warn.append(f"field '{k}' tidak ada (latency/packet-loss tidak terhitung)")
        elif not _num(pkt[k]):
            err.append(f"'{k}' harus angka, dapat {type(pkt[k]).__name__}")
    if _num(pkt.get("timestamp")):
        lat = (time.time() - float(pkt["timestamp"])) * 1000
        if not (0 <= lat < 10000):
            warn.append(f"latency {lat:.0f} ms di luar 0-10000 → jam RPi & PC belum sinkron (NTP)")

    t = pkt.get("type", "")
    if t == "button":
        if not isinstance(pkt.get("button"), int):
            err.append("'button' harus integer index")
        if pkt.get("value") not in (0, 1):
            err.append("'value' tombol harus 0/1")
        return "button", err, warn
    if t == "axis":
        if not isinstance(pkt.get("axis"), int):
            err.append("'axis' harus integer index")
        v = pkt.get("value")
        if not _num(v):
            err.append("'value' axis harus angka")
        elif not -1.0 <= v <= 1.0:
            warn.append(f"'value' axis {v} di luar -1.0..1.0")
        return "axis", err, warn

    if "buttons" in pkt:
        b = pkt["buttons"]
        if not isinstance(b, dict):
            err.append("'buttons' harus object")
        else:
            miss = [k for k in EXPECTED_BUTTONS if k not in b]
            extra = [k for k in b if k not in EXPECTED_BUTTONS]
            if miss:
                warn.append(f"tombol hilang: {miss}")
            if extra:
                warn.append(f"tombol tak dikenal (diabaikan GUI): {extra}")
            bad = [k for k, v in b.items() if v not in (0, 1, True, False)]
            if bad:
                err.append(f"nilai tombol bukan 0/1: {bad}")
        a = pkt.get("analog")
        if a is None:
            warn.append("'analog' tidak ada (LT/RT/stick tidak terbaca)")
        elif not isinstance(a, dict):
            err.append("'analog' harus object")
        else:
            miss = [k for k in EXPECTED_ANALOG if k not in a]
            if miss:
                warn.append(f"analog hilang: {miss}")
            for k, v in a.items():
                if not _num(v):
                    err.append(f"analog '{k}' bukan angka")
                elif k in ("LT", "RT") and not 0.0 <= v <= 1.0:
                    warn.append(f"{k}={v} di luar 0.0..1.0")
                elif k not in ("LT", "RT") and not -1.0 <= v <= 1.0:
                    warn.append(f"{k}={v} di luar -1.0..1.0")
        if "joystick_connected" not in pkt:
            warn.append("'joystick_connected' tidak ada (dianggap True)")
        return "heartbeat", err, warn

    if t == "heartbeat":
        warn.append("heartbeat tanpa 'buttons' (hanya keep-alive)")
        return "heartbeat", err, warn
    err.append(f"format tidak dikenal (type='{t}', tanpa 'buttons')")
    return "unknown", err, warn


def summary_line(kind, pkt):
    if kind == "heartbeat" and isinstance(pkt.get("analog"), dict):
        a, b = pkt["analog"], pkt.get("buttons", {})
        on = [k for k, v in b.items() if v] or ["-"]
        return (f"L({a.get('axis_1_x',0):+.2f},{a.get('axis_1_y',0):+.2f}) "
                f"R({a.get('axis_2_x',0):+.2f},{a.get('axis_2_y',0):+.2f}) "
                f"LT={a.get('LT',0):.2f} RT={a.get('RT',0):.2f} "
                f"BT={'ON' if pkt.get('joystick_connected', True) else 'OFF'} "
                f"btn={','.join(on)}")
    if kind in ("button", "axis"):
        return f"{kind}={pkt.get(kind)} value={pkt.get('value')}"
    return ""


def send_test(port):
    pkt = {"type": "heartbeat", "seq": 1, "timestamp": time.time(),
           "joystick_connected": True,
           "buttons": {k: 0 for k in EXPECTED_BUTTONS} | {"A": 1},
           "analog": {"LT": 0.0, "RT": 0.5, "axis_1_x": 0.3, "axis_1_y": -0.7,
                      "axis_2_x": 0.0, "axis_2_y": 0.0, "dpad_x": 0.0, "dpad_y": 0.0}}
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(json.dumps(pkt).encode(), ("127.0.0.1", port))
    print(f"Paket contoh terkirim ke 127.0.0.1:{port}\n{json.dumps(pkt, indent=2)}")


def main():
    ap = argparse.ArgumentParser(description="Cek format JSON payload UDP joystick")
    ap.add_argument("--port", type=int, default=load_port())
    ap.add_argument("--raw", action="store_true", help="tampilkan JSON mentah")
    ap.add_argument("--count", type=int, default=0, help="jumlah paket lalu stop")
    ap.add_argument("--send-test", action="store_true", help="kirim paket contoh")
    args = ap.parse_args()

    if args.send_test:
        return send_test(args.port)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", args.port))
    except OSError as e:
        sys.exit(f"{R}Gagal bind port {args.port}: {e}\nTutup GUI dulu.{X}")
    print(f"{C}Mendengarkan UDP di 0.0.0.0:{args.port} — Ctrl+C untuk berhenti{X}\n")

    n = ok = bad = malformed = 0
    t0 = last = time.monotonic()
    try:
        while not args.count or n < args.count:
            data, addr = s.recvfrom(65535)
            now = time.monotonic()
            n += 1
            dt = (now - last) * 1000
            last = now
            try:
                pkt = json.loads(data.decode("utf-8").strip())
            except Exception as e:
                malformed += 1
                print(f"{R}#{n} MALFORMED dari {addr[0]}: {e}{X}\n  {D}{data[:200]!r}{X}")
                continue
            kind, err, warn = validate(pkt)
            status = f"{R}ERROR{X}" if err else (f"{Y}WARN {X}" if warn else f"{G}OK   {X}")
            bad += bool(err)
            ok += not err
            print(f"#{n:<5} {status} {kind:<9} {D}{addr[0]} +{dt:5.1f}ms{X}  {summary_line(kind, pkt)}")
            for e in err:
                print(f"        {R}✗ {e}{X}")
            for w in warn:
                print(f"        {Y}! {w}{X}")
            if args.raw:
                print(D + json.dumps(pkt, indent=2) + X)
    except KeyboardInterrupt:
        pass
    el = max(time.monotonic() - t0, 1e-6)
    print(f"\n{C}Ringkasan:{X} total={n} valid={ok} error={bad} "
          f"malformed={malformed} rate≈{n/el:.1f} paket/s")


if __name__ == "__main__":
    main()
