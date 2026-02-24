#!/usr/bin/env python3
"""
Synchronise les photos d'un mémorial vers un dossier local en temps réel.
Envoie des messages OSC à TouchDesigner à chaque nouvelle photo.

Usage:
    python sync.py --event jean-tremblay
    python sync.py --event jean-tremblay --output ./photos --interval 10
    python sync.py --event jean-tremblay --osc-port 7000

TouchDesigner reçoit les messages OSC sur le port spécifié (défaut: 7000).
"""

import argparse
import json
import os
import socket
import struct
import sys
import time
import urllib.request
from datetime import datetime

BASE_URL = "https://hommage-funeraire-python.vercel.app"
DEFAULT_INTERVAL = 10   # secondes
DEFAULT_OSC_PORT = 7000
DEFAULT_OSC_HOST = "127.0.0.1"


# ── OSC (sans dépendances externes) ────────────────────────────────────────

def _osc_pad(data: bytes) -> bytes:
    pad = (4 - len(data) % 4) % 4
    return data + b'\x00' * pad

def _osc_str(s: str) -> bytes:
    return _osc_pad(s.encode('utf-8') + b'\x00')

def _osc_message(address: str, *args) -> bytes:
    """Encode un message OSC simple (strings et ints)."""
    tags = ','
    encoded_args = b''
    for a in args:
        if isinstance(a, str):
            tags += 's'
            encoded_args += _osc_str(a)
        elif isinstance(a, int):
            tags += 'i'
            encoded_args += struct.pack('>i', a)
        elif isinstance(a, float):
            tags += 'f'
            encoded_args += struct.pack('>f', a)
    return _osc_str(address) + _osc_str(tags) + encoded_args

class OSCSender:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, address: str, *args):
        try:
            self.sock.sendto(_osc_message(address, *args), (self.host, self.port))
        except Exception as e:
            log(f"  OSC erreur : {e}")

    def close(self):
        self.sock.close()


# ── Utils ───────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def fetch_urls(base_url, event):
    url = f"{base_url}/api/images?event={urllib.request.quote(event)}&t={int(time.time())}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "hommage-sync/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, list) else []
    except Exception as e:
        log(f"Erreur API : {e}")
        return []

def download(url, filepath):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "hommage-sync/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(filepath, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        log(f"  Erreur téléchargement : {e}")
        return False

def write_manifest(output_dir, event, new_files):
    files = sorted([f for f in os.listdir(output_dir) if not f.startswith("_")])
    manifest = {
        "event": event,
        "total": len(files),
        "files": files,
        "new": new_files,
        "updated": datetime.now().isoformat(),
    }
    with open(os.path.join(output_dir, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    with open(os.path.join(output_dir, "_new.json"), "w", encoding="utf-8") as f:
        json.dump({"files": new_files, "updated": manifest["updated"]}, f, indent=2)
    return manifest


# ── Sync principal ──────────────────────────────────────────────────────────

def sync(base_url, event, output_dir, interval, osc: OSCSender):
    os.makedirs(output_dir, exist_ok=True)
    known_urls = set()
    abs_output = os.path.abspath(output_dir)

    print("=" * 55)
    print("  Hommage Funéraire — Sync Local + TouchDesigner")
    print("=" * 55)
    print(f"  Événement  : {event}")
    print(f"  Dossier    : {abs_output}")
    print(f"  Intervalle : {interval}s")
    print(f"  OSC → {osc.host}:{osc.port}")
    print("=" * 55)
    print("  Ctrl+C pour arrêter\n")

    # Sync initial
    log("Connexion à l'API...")
    urls = fetch_urls(base_url, event)
    initial_files = []

    if not urls:
        log("Aucune photo pour le moment. En attente...")
    else:
        log(f"{len(urls)} photo(s) existante(s) — téléchargement initial...")
        for url in urls:
            filename = url.split("/")[-1].split("?")[0]
            filepath = os.path.join(output_dir, filename)
            if not os.path.exists(filepath):
                if download(url, filepath):
                    log(f"  ✓ {filename}")
                    initial_files.append(filename)
            known_urls.add(url)

        manifest = write_manifest(output_dir, event, initial_files)
        total = manifest["total"]
        abs_dir = abs_output.replace("\\", "/")

        # Notifie TD que le chargement initial est fait
        osc.send("/hommage/ready", event, total, abs_dir)
        for fname in initial_files:
            fpath = os.path.join(abs_output, fname).replace("\\", "/")
            osc.send("/hommage/new_photo", fpath, total)

        log(f"Sync initial terminé — {total} photo(s)\n")

    # Boucle principale
    while True:
        time.sleep(interval)
        urls = fetch_urls(base_url, event)
        new_urls = [u for u in urls if u not in known_urls]

        if not new_urls:
            log(f"{len(urls)} photo(s) — aucune nouvelle")
            continue

        log(f"↓ {len(new_urls)} nouvelle(s) photo(s) !")
        new_files = []

        for url in new_urls:
            filename = url.split("/")[-1].split("?")[0]
            filepath = os.path.join(output_dir, filename)
            if download(url, filepath):
                known_urls.add(url)
                new_files.append(filename)
                log(f"  ✓ {filename}")

        if new_files:
            manifest = write_manifest(output_dir, event, new_files)
            total = manifest["total"]
            abs_dir = abs_output.replace("\\", "/")
            for fname in new_files:
                fpath = os.path.join(abs_output, fname).replace("\\", "/")
                osc.send("/hommage/new_photo", fpath, total)
                log(f"  → OSC /hommage/new_photo {fpath}")


# ── Entrée ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sync photos mémorial → dossier local + OSC vers TouchDesigner"
    )
    parser.add_argument("--event", required=True,
                        help="Slug de l'événement (ex: jean-tremblay)")
    parser.add_argument("--output", default="./photos",
                        help="Dossier de sortie (défaut: ./photos)")
    parser.add_argument("--url", default=BASE_URL,
                        help=f"URL de base (défaut: {BASE_URL})")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help=f"Intervalle en secondes (défaut: {DEFAULT_INTERVAL})")
    parser.add_argument("--osc-host", default=DEFAULT_OSC_HOST,
                        help=f"Hôte OSC (défaut: {DEFAULT_OSC_HOST})")
    parser.add_argument("--osc-port", type=int, default=DEFAULT_OSC_PORT,
                        help=f"Port OSC TouchDesigner (défaut: {DEFAULT_OSC_PORT})")
    args = parser.parse_args()

    osc = OSCSender(args.osc_host, args.osc_port)
    try:
        sync(args.url, args.event, args.output, args.interval, osc)
    except KeyboardInterrupt:
        osc.close()
        print("\nSynchronisation arrêtée.")
        sys.exit(0)

if __name__ == "__main__":
    main()
